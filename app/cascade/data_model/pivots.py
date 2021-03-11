# NOTICE
#
# This software was produced for the U. S. Government
# under Basic Contract No. W15P7T-13-C-A802, and is
# subject to the Rights in Noncommercial Computer Software
# and Noncommercial Computer Software Documentation
# Clause 252.227-7014 (FEB 2012)
#
# (C) 2017 The MITRE Corporation.

import datetime
import logging

from app.cascade.data_model import pivot
from app.cascade.data_model.events import ProcessEvent, FileEvent, ModuleEvent, ThreadEvent, NetworkEvent, RegistryEvent

logger = logging.getLogger(__name__)


class Criteria(dict):
    def coalesce(self, state, *args, **kwargs):
        force = kwargs.pop('force', True)

        for arg in args:
            if arg in state:
                self[arg] = state[arg]
                return self

        if force:
            raise KeyError
        return self


@pivot.register(FileEvent, ['create', 'write', 'modify'], ProcessEvent, ['create'])
def file_execution(file_event, ctx=None):
    """ Pivots from a dropped file onto a process start. Cases include running a
    new process (i.e. new_file.exe) and loading it as a script (i.e. powershell -ep bypass .\evil.ps1).
    """
    window = {'start': file_event.time - datetime.timedelta(minutes=1)}

    criteria = Criteria(hostname=file_event.state.hostname)

    if file_event.state.file_path:
        criteria['image_path'] = file_event.state.file_path
    elif file_event.state.file_name:
        criteria['exe'] = file_event.state.file_name

    for result in ctx.query(ProcessEvent.search(action='create', **criteria), **window):
        yield ProcessEvent.update_existing(action='create', **result)


# @pivot.register(FileEvent, ['create', 'write', 'modify'], ModuleEvent, ['load'])
# def file_loaded_as_module(file_event, ctx=None):
#     """
#     Pivots from a dropped file onto a DLL load event by any process.
#     """
#     raise NotImplementedError
#

@pivot.register(NetworkEvent, ["message"], NetworkEvent, ["start"], reverse=True)
def group_messages(network_event, ctx=None):
    """ Given a suspicious connection, determine the process(es) on each endpoint
    of the connection. This will resolve the processes, but will not look for
    creation or termination events. As a result, it will not pivot onto the
    launched child processes of the other endpoints. This would avoid investigating
    on the legitimate half a connection, but be informational in detecting the
    responsible process.
    """

    # Find the most recent creation event for this pid
    state = network_event.state
    src_ip, src_port, = state.src_ip, state.src_port
    dest_ip, dest_port = state.dest_ip, state.dest_port

    if 'hostname' in state:
        criteria = Criteria(hostname=state.hostname)
        flow_query = NetworkEvent.search(action='start', **criteria)
        flow_query = flow_query & (
            NetworkEvent.search('start', src_ip=src_ip, src_port=src_port, dest_ip=dest_ip, dest_port=dest_port) |
            NetworkEvent.search('start', src_ip=dest_ip, src_port=dest_port, dest_ip=src_ip, dest_port=src_port)
        )

        for result in ctx.query(flow_query, last=1, end=network_event.time + datetime.timedelta(minutes=1)):
            resolved_flow = NetworkEvent.update_existing(action='state', **result)
            yield resolved_flow


@pivot.register(ProcessEvent, ['create', 'inject'], ProcessEvent, ['terminate'])
def process_end(process_event, ctx=None):
    """ Given a process creation, lookup the termination to gather the end time.
    The difference on the two may be used to calculate the duration.

    This pivot should be performed first, which will ensure that other pivots have a better window,
    knowing both start and end time. Thus it must not be performed asynchronously

    :type process_event: ProcessEvent
    """
    terminate_window = {'start': process_event.time - datetime.timedelta(seconds=1)}

    # Get the time where the pid is reused (if it is)
    criteria = Criteria(pid=process_event.state.pid, hostname=process_event.state['hostname'])

    reuse_query = ctx.query(ProcessEvent.search(action='create', **criteria),
                            first=1, start=process_event.time + datetime.timedelta(minutes=5))

    for result in reuse_query:
        reused_pid = ProcessEvent.update_existing(action='create', **result)

        # Round the time down more
        terminate_window['end'] = max(reused_pid.time - datetime.timedelta(minutes=10),
                                      process_event.time + datetime.timedelta(seconds=1))

    # Now shrink the window, knowing when the pid is reused. Look for the correct terminate event
    terminate_query = ctx.query(ProcessEvent.search(action='terminate', **criteria), first=1, **terminate_window)

    for result in terminate_query:
        # Update with the original fields from the 'create' event
        state = process_event.state.to_mongo().to_dict()
        state.update(result['state'])
        result['state'] = state

        process_terminate = ProcessEvent.update_existing(action='terminate', **result)

        # Calculate the duration and update the parent
        duration = process_terminate.time - process_event.time
        # for sanity's sake, avoid non-zero duration (if logs came in at the same time)
        duration = datetime.timedelta(seconds=1) if duration.total_seconds() == 0 else duration
        process_event.duration = duration

        yield process_terminate

    if process_event.duration is None:
        if terminate_window.get('end', None) is not None:
            logger.warning('[PIVOTS] No end time detected, using time of pid reuse')
            duration = terminate_window['end'] - process_event.time
            # process will auto-update state.duration
            process_event.duration = duration


@pivot.register(ProcessEvent, ['create', 'inject'], ProcessEvent, ['create'], depends=['process_end'])
def child_process(process_event, ctx=None):
    """ Pivots from the creation of a process, to all spawned child processes.
    :type process_event: ProcessEvent
    """
    window = {'start': process_event.time - datetime.timedelta(minutes=1)}
    if process_event.duration is not None:
        window['end'] = process_event.time + process_event.duration + datetime.timedelta(minutes=1)

    criteria = Criteria(ppid=process_event.state.pid, hostname=process_event.state.hostname)

    # try to filter this out further to make a more precise query
    if process_event.state.parent_image_path and process_event.state.image_path:
        criteria['parent_image_path'] = process_event.state.image_path
    elif process_event.state.parent_exe and process_event.state.exe:
        criteria['parent_exe'] = process_event.state.exe

    query = ctx.query(ProcessEvent.search(action='create', **criteria), **window)

    for result in query:
        child_event = ProcessEvent.update_existing(action='create', **result)
        child_event.parent = process_event
        child_event.save()
        yield child_event


@pivot.register(ProcessEvent, ['create', 'inject'], ProcessEvent, ['create'], reverse=True, inverse='child_process')
def lookup_parent(process_event, ctx=None):
    """ Given a process creation, try to find the parent process. In this case, pid reuse shouldn't be a problem.
    Unless there is a missing gap of data.
    :type process_event: ProcessEvent
    """

    # Get the time where the pid is reused (if it is)
    if 'ppid' in process_event.state:
        criteria = Criteria(pid=process_event.state.ppid, hostname=process_event.state.hostname)

        # If this event has the process field, then it is likely the next one will
        if process_event.state.parent_image_path:
            criteria['image_path'] = process_event.state.parent_image_path
        elif process_event.state.parent_exe:
            criteria['exe'] = process_event.state.parent_exe

        parent_query = ProcessEvent.search(action='create', **criteria)

        for result in ctx.query(parent_query, last=1, end=process_event.time + datetime.timedelta(minutes=1)):
            parent_process = ProcessEvent.update_existing(action='create', **result)
            yield parent_process


@pivot.register(ProcessEvent, ['create', 'inject'], NetworkEvent, ['start'], depends=['process_end'])
def network_connection(process_event, ctx=None):
    """ Given a process creation, find all connections (incoming or outgoing) the process created.
    :type process_event: ProcessEvent
    """
    window = {'start': process_event.time - datetime.timedelta(minutes=2)}
    if process_event.duration is not None:
        window['end'] = process_event.time + process_event.duration + datetime.timedelta(minutes=2)

    criteria = Criteria(pid=process_event.state.pid, hostname=process_event.state.hostname)
    query = ctx.query(NetworkEvent.search(action='start', **criteria), **window)

    connections = {}
    for result in sorted(query, key=lambda x: x['time']):
        flow = NetworkEvent.update_existing(action='start', **result)
        # Multiple sensors might log the same flow but have a partial set of fields
        # These should be unified instead
        conn_id = flow.undirected_connection_id
        if conn_id in connections:

            # Should the key here be the undirected version??
            matching_flow = connections[conn_id]
            for field in NetworkEvent.fields:
                # Grab the other connection information, such as src_hostname
                if field.startswith('src_') or field.startswith('dest_'):
                    if matching_flow.state[field] is None and flow.state[field] is not None:
                        matching_flow.state[field] = flow.state[field]

                # If it is other message-like information, then flatten these
                elif field in ('content', 'proto_info'):
                    if flow.state[field] is not None and matching_flow.state[field] is not None:
                        matching_flow.state[field] = matching_flow.state[field] + flow.state[field] + '\n'

            matching_flow.time = min(matching_flow.time, flow.time)
            matching_flow.save()

            # Return each flow individually
            # This includes each packet detected by hostflow
            # continue
        else:
            connections[conn_id] = flow
            yield flow


@pivot.register(ProcessEvent, ['create', 'inject'],
                RegistryEvent, ['create_key', 'delete_key', 'rename_key'], depends=['process_end'])
def registry_key_modification(process_event, ctx=None):
    """ Given a process creation, find all registry modifications.
    :type process_event: ProcessEvent
    """
    window = {'start': process_event.time - datetime.timedelta(minutes=2)}
    if process_event.duration is not None:
        window['end'] = process_event.time + process_event.duration + datetime.timedelta(minutes=2)

    criteria = Criteria(pid=process_event.state.pid, hostname=process_event.state.hostname)

    for action in ('create_key', 'delete_key', 'rename_key'):
        for result in ctx.query(RegistryEvent.search(action=action, **criteria), **window):
            reg_event = RegistryEvent.update_existing(action=action, **result)
            for field in ('parent_image_path', 'pid', 'ppid', 'image_path', 'exe', 'parent_exe', 'user', 'fqdn'):
                # Update missing fields from the process
                if process_event.state[field] and reg_event.state[field] is None:
                    reg_event.state[field] = process_event.state[field]
                yield reg_event


@pivot.register(ProcessEvent, ['create', 'inject'], RegistryEvent, ['write_value', 'delete_value'], depends=['process_end'])
def registry_value_modification(process_event, ctx=None):
    """ Given a process creation, find all registry modifications.
    :type process_event: ProcessEvent
    """
    window = {'start': process_event.time - datetime.timedelta(minutes=2)}
    if process_event.duration is not None:
        window['end'] = process_event.time + process_event.duration + datetime.timedelta(minutes=2)

    criteria = Criteria(pid=process_event.state.pid, hostname=process_event.state.hostname)

    for action in ('write_value', 'delete_value'):
        for result in ctx.query(RegistryEvent.search(action=action, **criteria), **window):
            reg_event = RegistryEvent.update_existing(action=action, **result)
            for field in ('parent_image_path', 'pid', 'ppid', 'image_path', 'exe', 'parent_exe', 'user', 'fqdn'):
                # Update missing fields from the process
                if process_event.state[field] and reg_event.state[field] is None:
                    reg_event.state[field] = process_event.state[field]
            yield reg_event


@pivot.register(ProcessEvent, ['create', 'inject'], RegistryEvent, ['read_value'], depends=['process_end'])
def registry_read_value(process_event, ctx=None):
    """ Given a process creation, find all registry modifications.
    :type process_event: ProcessEvent
    """
    window = {'start': process_event.time - datetime.timedelta(minutes=2)}
    if process_event.duration is not None:
        window['end'] = process_event.time + process_event.duration + datetime.timedelta(minutes=2)

    criteria = Criteria(pid=process_event.state.pid, hostname=process_event.state.hostname)

    action = 'read_value'
    for result in ctx.query(RegistryEvent.search(action=action, **criteria), **window):
        reg_event = RegistryEvent.update_existing(action=action, **result)
        for field in ('parent_image_path', 'pid', 'ppid', 'image_path', 'exe', 'parent_exe', 'user', 'fqdn'):
            # Update missing fields from the process
            if process_event.state[field] and reg_event.state[field] is None:
                reg_event.state[field] = process_event.state[field]
        yield reg_event


@pivot.register(RegistryEvent, ['write_value'], ProcessEvent, ['create', 'inject'])
def registry_key_run(registry_event, ctx=None):
    """ Given a process creation, find all registry modifications.
    :type process_event: ProcessEvent
    """
    if not registry_event.state.data:
        return

    data = registry_event.state.data
    window = {'start': registry_event.time - datetime.timedelta(minutes=2)}

    query = ProcessEvent.search(action='create', image_path=data) | ProcessEvent.search(action='create', command_line=data)
    for result in ctx.query(query, **window):
        yield ProcessEvent.update_existing(action='create', **result)


@pivot.register(ProcessEvent, ['create', 'inject'], FileEvent, ['create', 'write', 'modify'], depends=['process_end'])
def file_modification(process_event, ctx=None):
    """ Given a process creation, find all file system modifications.
    :type process_event: ProcessEvent
    """
    window = {'start': process_event.time - datetime.timedelta(minutes=1)}
    if process_event.duration is not None:
        window['end'] = process_event.time + process_event.duration + datetime.timedelta(minutes=1)

    for action in ('create', 'write', 'modify'):
        criteria = Criteria(pid=process_event.state.pid, hostname=process_event.state.hostname)
        query = ctx.query(FileEvent.search(action, **criteria), **window)

        for result in query:
            file_event = FileEvent.update_existing(action=action, **result)
            for field in ('pid', 'ppid', 'exe', 'image_path'):
                if file_event.state[field] is None and process_event.state[field]:
                    file_event.state[field] = process_event.state[field]

            file_event.save()
            yield file_event


@pivot.register(NetworkEvent, NetworkEvent.actions, ProcessEvent, ["create"], reverse=True, inverse='network_connection', name='get_network_context')
@pivot.register(ModuleEvent, ModuleEvent.actions, ProcessEvent, ["create"], reverse=True, inverse='file_modification', name='get_module_context')
@pivot.register(FileEvent, FileEvent.actions, ProcessEvent, ["create"], reverse=True, inverse='file_modification', name='get_file_context')
@pivot.register(RegistryEvent, RegistryEvent.actions, ProcessEvent, ["create"], reverse=True, name='get_registry_context')
def get_process_context(event, ctx=None):
    """ Identifies the process event that corresponds to the pid and hostname of another generic DataModelEvent

    :param DataModelEvent event:
    :param ctx:
    :return:
    """
    if 'pid' in event.state:
        criteria = Criteria(hostname=event.state.hostname, pid=event.state.pid)
        criteria.coalesce(event.state, 'image_path', 'exe', force=False)
        process_query = ProcessEvent.search(action='create', **criteria)

        for result in ctx.query(process_query, last=1, end=event.time + datetime.timedelta(minutes=1)):
            resolved_process = ProcessEvent.update_existing(action='create', **result)
            yield resolved_process
