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

from app.cascade.data_model.events import ProcessEvent, FileEvent, NetworkEvent, ThreadEvent, RegistryEvent
from app.cascade.data_model.query import FieldQuery
from app.cascade.data_model import pivot
from app.cascade.data_model.pivots import Criteria
from app.utils import command_to_argv, next_arg

logger = logging.getLogger(__name__)


def extract_host(host_string):
    prefix = '\\\\'
    host_info = {}
    if host_string.startswith(prefix):
        host_string = host_string[len(prefix):]
    if "." in host_string:
        try:
            ip_list = [int(_) for _ in host_string.split('.')]
            if len(ip_list) == 4:
                host_info['ip_address'] = host_string
        except ValueError:
            host_info['fqdn'] = host_string
            host_info['hostname'] = host_string.split(".")[0]
    else:
        host_info['hostname'] = host_string.split(".")[0]
    return host_info


@pivot.register(ProcessEvent, ['create', 'inject'], ThreadEvent, ['remote_create'], depends=['process_end'])
def thread_inject(process_event, ctx=None):
    """ Given a suspicious process, detects all processes that it injected into.
    A more complex pivot, because the destination may also act legitimately
    if the prior threads were not tampered with. Thus, this may require
    greater granularity (thread level) in order to better resolve its pivots
    to ignore those that were benign.
    :type process_event: Process
    """
    window = {'start': process_event.time - datetime.timedelta(minutes=1)}
    if process_event.duration is not None:
        window['end'] = process_event.time + process_event.duration + datetime.timedelta(minutes=1)

    # Ignore thread creations into the kernel
    criteria = Criteria(src_pid=process_event.state.pid)
    criteria['hostname'] = process_event.state.hostname
    terms = ThreadEvent.search('remote_create', **criteria) & (
        FieldQuery("target_pid").wildcard("*") & (FieldQuery('target_pid') != 4)
    )

    for result in ctx.query(terms, **window):
        remote_thread = ThreadEvent.update_existing(action='remote_create', **result)
        for process_field in ProcessEvent.fields:
            if process_event.state[process_field] is not None:
                thread_field = 'src_' + process_field
                if thread_field in ThreadEvent.fields and thread_field not in remote_thread.state:
                    remote_thread.state[thread_field] = process_event.state[process_field]

        remote_thread.save()
        yield remote_thread


@pivot.register(ThreadEvent, ['remote_create'], ProcessEvent, ["create"], reverse=True, inverse='thread_inject')
def injection_source(thread_event, ctx=None):
    """ Given a suspicious thread, determine the process(es) on each endpoint
    of the connection. This will resolve the processes, but will not look for
    creation or termination events. As a result, it will not pivot onto the
    launched child processes of the other endpoints. This would avoid investigating
    on the legitimate half a connection, but be informational in detecting the
    responsible process.
    """

    # Find the most recent creation event for this pid

    criteria = Criteria()

    if 'src_pid' in thread_event.state:
        criteria['hostname'] = thread_event.state.hostname
        src_fields = {k.split("src_").pop(): v for k, v in thread_event.state.to_mongo().items() if k.startswith("src_")}
        criteria.coalesce(src_fields, 'image_path', 'exe', force=False)
        criteria.coalesce(src_fields, 'parent_image_path', 'parent_exe', force=False)
        criteria.coalesce(src_fields, 'ppid', force=False)

        parent_query = ProcessEvent.search(action='create', **criteria)

        for result in ctx.query(parent_query, last=1, end=thread_event.time + datetime.timedelta(minutes=1)):
            resolved_process = ProcessEvent.update_existing(action='create', **result)
            yield resolved_process


@pivot.register(ThreadEvent, ['remote_create'], ProcessEvent, ['inject'], abstract=True)
def tainted_process(thread_event, ctx):
    """ Given a thread injection event, taint the process from that point forward.
    :type thread_event: Thread
    """
    # The process must have existed by the time the remote thread was created
    window = {'end': thread_event.time + datetime.timedelta(minutes=1), 'last': 1}
    criteria = Criteria(pid=thread_event.state.target_pid)
    criteria['hostname'] = thread_event.state.hostname

    # filter down the process if possible
    if 'target_image_path' in thread_event.state:
        criteria['image_path'] = thread_event.state.target_image_path
    elif 'target_exe' in thread_event.state:
        criteria['exe'] = thread_event.state.target_exe

    query = ctx.query(ProcessEvent.search(action='create', **criteria), **window)

    for result in query:
        # taint the process immediately before the injection occurred (to be safe)
        result['time'] = thread_event.time - datetime.timedelta(seconds=1)
        injected_process = ProcessEvent.update_existing(action='inject', **result)

        # Once the creation event has been detected, update the injection event with the target information
        # from the target process
        for field in injected_process.state:
            thread_field = 'target_' + field
            if thread_field in ThreadEvent.fields and thread_field not in thread_event.state:
                thread_event.state[thread_field] = injected_process.state[field]
            thread_event.save()

        injected_process.save()
        yield injected_process
        break

    # However, if the process creation can not be found, then make up an injection event
    else:
        process_info = {}
        if thread_event.state.fqdn:
            process_info['fqdn'] = thread_event.state.fqdn
        if thread_event.state.hostname:
            process_info['hostname'] = thread_event.state.hostname

        for field in ProcessEvent.fields:
            thread_field = 'target_' + field
            if thread_field in thread_event.state:
                process_info[field] = thread_event.state[thread_field]

        inject_time = thread_event.time
        fake_injected = ProcessEvent.update_existing(action='inject', metadata={'synthetic': True}, state=process_info, time=inject_time)
        logger.warning('Process create not found. Fabricating injection event!')
        yield fake_injected


@pivot.register(NetworkEvent, ['message'], FileEvent, ['create', 'modify'], abstract=True)
def smb_file_write(network_event, ctx):
    """ Given a flow event that has protocol information, pivot from host information into the file event on the
    host. If it doesn't exist, then add

    """
    if network_event.state.proto_info is None:
        return

    if network_event.state.proto_info.startswith('SMB2 Write Request') and 'File: ' in network_event.state.proto_info:
        relative_path = network_event.state.proto_info.split('File: ').pop()
        relative_path = relative_path.split(';')[0]
        relative_path = relative_path.split('#')[0]

        # Filter out writes to NamedPipes over SMB
        if not ('.' in relative_path or '\\' in relative_path):
            return

        wildcard_path = '*\\' + relative_path
        files = []
        window = {'start': network_event.time - datetime.timedelta(seconds=10), 'end': network_event.time + datetime.timedelta(minutes=1)}

        criteria = Criteria(file_path=wildcard_path)
        criteria['hostname'] = network_event.state.hostname
        # Grab the first file event if exists
        for action in ('create', 'modify'):
            for result in ctx.query(FileEvent.search(action=action, **criteria), **window):
                file_obj = FileEvent.update_existing(action, **result)
                yield file_obj
                # One per action is enough
                files.append(file_obj)
                break

        # Create a fake one if none can be found
        if len(files) == 0:

            file_fields = dict(file_path=wildcard_path, file_name=wildcard_path.split('\\').pop())
            for field in ('fqdn', 'hostname'):
                if network_event.state[field]:
                    file_fields[field] = network_event.state[field]
            yield FileEvent.update_existing('create', time=network_event.time + datetime.timedelta(seconds=1), state=file_fields, metadata={'synthetic': True})


@pivot.register(FileEvent, ['create', 'modify'], FileEvent, ['create', 'modify'], abstract=True)
def remote_file_modify(file_event, ctx):
    """ Detect file writes to a network share by looking for file events that look similar to
    \\host\share\relative\path\to\file.extension

    Pivot onto the other host to find the corresponding file event. If ony can't be found, fabricate this event
    """
    file_path = file_event.state.file_path
    if file_path and file_path.startswith('\\\\'):
        file_path = file_path[len('\\\\'):]
        # Not sure exactly what this means...
        if file_path.startswith(';LanmanRedirector'):
            file_path = '\\'.join(file_path.split('\\')[2:])
        host, share = file_path.split('\\')[:2]
        relative_path = '\\'.join(file_path.split('\\')[2:])
        drive = '*'
        if len(share) == 2 and share.endswith('$'):
            drive = share[0].upper() + ':'
        query = Criteria(file_path='{}\\{}'.format(drive, relative_path), file_name=relative_path.split('\\').pop())

        # File accesses can also be notated as \\?\C:\Windows\...
        if host == '?':
            return

        # Confirm that the hostname isn't actually an IP address
        host_info = extract_host(host)
        if 'hostname' in host_info:
            query['hostname'] = host_info['hostname']

        # Makes the assumption that the clocks between the host are fairly similar
        start_time = file_event.time - datetime.timedelta(seconds=10)
        end_time = file_event.time + datetime.timedelta(minutes=1)
        for remote_file_event in ctx.query(FileEvent.search(file_event.action, **query), start=start_time, end=end_time):
            remote_file = FileEvent.update_existing(file_event.action, **remote_file_event)
            yield remote_file
            break

        else:
            # if no file events can be found, then make one up
            file_time = file_event.time + datetime.timedelta(seconds=3)
            remote_file = FileEvent.update_existing(file_event.action, state=query, time=file_time, metadata={'synthetic': True})
            yield remote_file


@pivot.register(ProcessEvent, ['create'], ProcessEvent, ['create'], abstract=True)
def schtasks(process_event, ctx):
    """ :type process_event: Process """
    if process_event.state.exe.lower() == "schtasks.exe" and "/tr" in str(process_event.state.command_line).lower():
        args = command_to_argv(process_event.state.command_line)
        lower_args = [_.lower() for _ in args]
        criteria = Criteria()

        # if scheduling a task on a remote system, extract out fqdn or hostname (but could be IP)
        if "/s" in lower_args:
            host = next_arg(args, "/s")
            if host:
                host_info = extract_host(host)
                if 'hostname' in host_info:
                    criteria['hostname'] = host_info['hostname']

        else:
            # if the system is not directly defined, then the host stays the same
            criteria['hostname'] = process_event.state.hostname

        # now extract out the task to be run from the command line
        task_run = next_arg(args, "/tr")
        if task_run is None:
            return

        logger.debug("Pivoting onto scheduled task with command line {}".format(task_run))

        query = ProcessEvent.search('create', **criteria) & FieldQuery('command_line').wildcard('*' + task_run + '*') & (
            (FieldQuery("parent_image_path") == "C:\\Windows\\System32\\taskeng.exe") |
            (FieldQuery("parent_image_path") == "C:\\Windows\\System32\\svchost.exe")
        )

        for process_event in ctx.query(query, start=process_event.time):
            task_process = ProcessEvent.update_existing('create', **process_event)
            yield task_process


@pivot.register(ProcessEvent, ['create'], ProcessEvent, ['create'], abstract=True)
def at(process_event, ctx):
    """ :type process_event: Process """

    if process_event.state.exe.lower() == "at.exe" and "/?" not in str(process_event.state.command_line):
        args = command_to_argv(process_event.state.command_line)
        lower_args = [_.lower() for _ in args]
        if len(args) == 1:
            return

        criteria = Criteria()  # parent_exe="taskeng.exe". This may not be true in windows 8
        if len(args) > 2 and args[1].startswith("\\\\"):
            host_string = args[1]
            host_info = extract_host(host_string)
            if 'hostname' in host_info:
                criteria['hostname'] = host_info['hostname']

        else:
            # if the system is not directly defined, then the host stays the same
            criteria['hostname'] = process_event.state.hostname

        if lower_args[-1] in ('/delete', '/yes'):
            return

        # Get the case version of the command
        command = args[-1]
        logger.debug("Pivoting onto AT command with command line {}".format(command))
        criteria['command_line'] = command

        query = ProcessEvent.search('create', **criteria) & (
            (FieldQuery("parent_image_path") == "C:\\Windows\\system32\\taskeng.exe") |
            (FieldQuery("parent_image_path") == "C:\\Windows\\system32\\svchost.exe")

        )
        for process_event in ctx.query(query, start=process_event.time):
            task_process = ProcessEvent.update_existing('create', **process_event)
            yield task_process


@pivot.register(ProcessEvent, ['create'], ProcessEvent, ['create'], abstract=True)
def wmic_process_create(process_event, ctx):
    """
    :param Process process_event: The input event to pivot on
    :param DataModelQueryLayer ctx: Search context to query over
    """

    if process_event.state.exe.lower() == "wmic.exe":
        args = command_to_argv(process_event.state.command_line)
        lower_args = [_.lower() for _ in args]

        if not ("process" in lower_args and "call" in lower_args and "create" in lower_args):
            return

        criteria = Criteria(parent_image_path="C:\\Windows\\System32\\wbem\\WmiPrvSE.exe")
        for arg in args:
            if arg.lower().startswith("/node:"):
                wmi_node = arg.split(":").pop().replace('"', '')
                host_info = extract_host(wmi_node)
                if 'hostname' in host_info:
                    criteria['hostname'] = host_info['hostname']
                break

        else:
            # if the system is not directly defined, then the host stays the same
            criteria['hostname'] = process_event.state.hostname

        wmic_command = next_arg(args, "create")
        if wmic_command is None:
            return

        # Get the case version of the command
        logger.debug("Pivoting onto WMIC command with command line {}".format(wmic_command))
        criteria['command_line'] = wmic_command

        for process_event in ctx.query(ProcessEvent.search('create', **criteria),
                                       start=process_event.time - datetime.timedelta(seconds=10),
                                       end=process_event.time + datetime.timedelta(minutes=1)):
            task_process = ProcessEvent.update_existing('create', **process_event)
            yield task_process


@pivot.register(ProcessEvent, ['create'], ProcessEvent, ['create'], abstract=True)
def sc(process_event, ctx):
    """ :type process_event: Process """

    if process_event.state.exe.lower() == "sc.exe" and "binpath=" in str(process_event.state.command_line.lower()):
        args = command_to_argv(process_event.state.command_line)

        criteria = Criteria(parent_image_path="C:\\windows\\system32\\services.exe")
        if len(args) > 2 and args[1].startswith("\\\\"):
            host_string = args[1]
            host_info = extract_host(host_string)
            if 'hostname' in host_info:
                criteria['hostname'] = host_info['hostname']

        else:
            # if the system is not directly defined, then the host stays the same
            criteria['hostname'] = process_event.state.hostname

        # Get the case version of the command
        bin_path = next_arg(args, "binPath=")
        if bin_path is None:
            return

        logger.debug("Pivoting onto SC command with command line {}".format(bin_path))
        criteria['command_line'] = bin_path.replace("'", '"')

        for process_event in ctx.query(ProcessEvent.search('create', **criteria), start=process_event.time):
            task_process = ProcessEvent.update_existing('create', **process_event)
            yield task_process


@pivot.register(NetworkEvent, ["start"], NetworkEvent, ["start"], abstract=True)
def mapped_rpc(network_event, ctx):
    if network_event.state.dest_port == '135' and 'pid' in network_event.state:
        window = {'start': network_event.time - datetime.timedelta(seconds=1), 'end': network_event.time + datetime.timedelta(seconds=10)}
        criteria = Criteria(pid=network_event.state.pid, src_ip=network_event.state.src_ip, dest_ip=network_event.state.dest_ip)
        criteria['hostname'] = network_event.state.hostname

        # Ignore thread creations into the kernel
        query = ctx.query(NetworkEvent.search('start', **criteria), **window)

        for result in query:
            pivot_flow = NetworkEvent.update_existing('start', **result)

            if int(pivot_flow.state.dest_port) >= 49152 and int(pivot_flow.state.src_port) >= 49152:
                # Update the fields that don't exist
                for field in NetworkEvent.fields:
                    if field not in pivot_flow.state and network_event.state[field] is not None:
                        pivot_flow.state[field] = network_event.state[field]

                pivot_flow.save()
                yield pivot_flow


@pivot.register(ProcessEvent, ["create"], FileEvent, ["create"], abstract=True)
def cmd_copy(process_event, ctx):
    """
    :param Process process_event: The input event to pivot on
    :param DataModelQueryLayer ctx: Search context to query over
    """
    window = {'start': process_event.time - datetime.timedelta(minutes=1)}
    if process_event.duration is not None:
        window['end'] = process_event.time + process_event.duration + datetime.timedelta(minutes=1)

    if process_event.state.exe.lower() == 'cmd.exe' and 'copy' in process_event.state.command_line.lower():
        args = command_to_argv(process_event.state.command_line)
        lower_args = [_.lower() for _ in args]

        if len(lower_args) >= 5 and lower_args[1] == '/c' and lower_args[2] == 'copy':
            copy_args = args[3:]
            flags = ('/A', '/B', '/D', '/V', '/N', '/Y', '/-Y', '/Z', '/L')
            copy_args = [_ for _ in copy_args if _.upper() not in flags]
            if len(copy_args) != 2:
                return

            source_file, dest_file = copy_args

            # TODO: get rid of this quick fix for when network paths show up starting with '\' insted of '\\'
            if dest_file[0] == '\\' and dest_file[1] != '\\':
                dest_file = '\\' + dest_file

            file_events = []

            criteria = Criteria()
            criteria['hostname'] = process_event.state.hostname
            criteria['file_path'] = dest_file

            file_query = FileEvent.search('create', **criteria) & (
                (FieldQuery("pid") == process_event.state.pid) | (FieldQuery("pid") == 4)
            )

            # Grab the first file event if exists
            for result in ctx.query(file_query, **window):
                file_event = FileEvent.update_existing('create', **result)
                # One per action is enough
                file_events.append(file_event)
                yield file_event

            # Create a fake one if none can be found
            if len(file_events) == 0:
                file_fields = dict(file_path=dest_file, file_name=dest_file.split('\\').pop())
                for field in ('fqdn', 'hostname', 'pid', 'exe', 'image_path', 'pid', 'ppid'):
                    if process_event.state[field]:
                        file_fields[field] = process_event.state[field]
                yield FileEvent.update_existing('create', time=process_event.time + datetime.timedelta(seconds=1), state=file_fields, metadata={'synthetic': True})

