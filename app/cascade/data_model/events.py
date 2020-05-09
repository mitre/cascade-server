# NOTICE
#
# This software was produced for the U. S. Government
# under Basic Contract No. W15P7T-13-C-A802, and is
# subject to the Rights in Noncommercial Computer Software
# and Noncommercial Computer Software Documentation
# Clause 252.227-7014 (FEB 2012)
#
# (C) 2017 The MITRE Corporation.

from .event import DataModelEvent, event_lookup
import datetime


class ApiEvent(DataModelEvent):
    object_name = 'api'
    actions = [
        "call"
    ]
    fields = [
        "arguments",  # this will be a dict
        "function",
        "module",
        "return",
        # context fields
        "exe",
        "fqdn",
        "hostname",
        "image_path",
        "parent_exe",
        "parent_image_path",
        "pid",
        "ppid",
        "user"
    ]


class DriverEvent(DataModelEvent):
    object_name = 'driver'
    actions = [
        "load",
        "unload"
    ]
    fields = [
        "base_address",
        "fqdn",
        "hostname",
        "md5_hash",
        "module_name",
        "module_path",
        "publisher",
        "sha1_hash",
        "sha256_hash"
    ]


class FileEvent(DataModelEvent):
    object_name = 'file'
    actions = [
        "create",
        "delete",
        "modify",
        "read",
        "raw_access",
        "timestomp",
        "write"
    ]
    fields = [
        "company",
        "creation_time",
        "file_name",
        "file_path",
        "fqdn",
        "hostname",
        "md5_hash",
        "previous_creation_time",
        "sha1_hash",
        "signer",
        "sha256_hash",
        "user",
        "image_path",
        "exe",
        "pid",
        "ppid",
    ]
    identifiers = [
        "file_name",
    ]


class NetworkEvent(DataModelEvent):
    object_name = 'flow'
    actions = [
        "start",
        "end",
        "message"
    ]
    fields = [
        "content",
        "dest_fqdn",
        "dest_hostname",
        "dest_ip",
        "dest_port",
        "end_time",
        "exe",
        "flags",
        "fqdn",
        "hostname",
        "image_path",
        "mac",
        "packet_count",
        "pid",
        "ppid",
        "proto_info",
        "protocol",
        "src_fqdn",
        "src_hostname",
        "src_ip",
        "src_port",
        "start_time",
        "user"
    ]
    identifiers = [
        "src_ip",
        "src_port",
        "dest_ip",
        "dest_port",
        "pid",
        "proto_info"
    ]

    @property
    def connection_id(self):
        return str((self.state.src_ip, self.state.src_port, self.state.dest_ip, self.state.dest_port))

    @property
    def undirected_connection_id(self):
        src = (self.state.src_ip, self.state.src_port)
        dest = (self.state.dest_ip, self.state.dest_port)
        sorted_pair = str((min(src, dest), max(src, dest)))
        return sorted_pair


class ModuleEvent(DataModelEvent):
    object_name = 'module'
    actions = [
        "load",
        "unload"
    ]
    fields = [
        "base_address",
        "fqdn",
        "exe",
        "hostname",
        "image_path",
        "md5_hash",
        "module_path",
        "module_name",
        "pid",
        "publisher",
        "sha1_hash",
        "sha256_hash",
        "tid"
    ]
    identifiers = [
        "pid",
        "module_name"
    ]


class ProcessEvent(DataModelEvent):
    object_name = 'process'
    actions = [
        "create",
        "terminate",
        "inject"
    ]
    fields = [
        "command_line",
        "current_directory",
        "duration",
        "exe",
        "fqdn",
        "hostname",
        "image_path",
        "integrity_level",
        "md5_hash",
        "parent_exe",
        "parent_command_line",
        "parent_image_path",
        "pid",
        "ppid",
        "sha1_hash",
        "sha256_hash",
        "sid",
        "terminal_session_id",
        "user"
    ]
    identifiers = [
        "pid"
    ]

    def __init__(self, *args, **kwargs):
        super(ProcessEvent, self).__init__(*args, **kwargs)
        self._parent = None

    @property
    def end_time(self):
        return self.time + self.state.duration

    @property
    def duration(self):
        if 'duration' in self.state:
            return datetime.timedelta(seconds=self.state.duration)

    @duration.setter
    def duration(self, value):
        """:type value: datetime.timedelta"""
        duration = value.total_seconds()
        self.modify(state__duration=duration)

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent_process):
        """ :type parent_process: ProcessEvent """
        if parent_process is not None:
            assert isinstance(parent_process, ProcessEvent)

            if parent_process.state.image_path is not None:
                self.state.parent_image_path = parent_process.state.image_path

            if parent_process.state.exe is not None:
                self.state.parent_exe = parent_process.state.exe

            if parent_process.state.pid is not None:
                self.state.ppid = parent_process.state.pid

        self._parent = parent_process


class RegistryEvent(DataModelEvent):
    object_name = 'registry'
    actions = [
        # Key Operations
        "create_key",    # CreateSubKey
        "delete_key",    # DeleteSubKey
        "rename_key",    # RenameKey
        # Value Operations
        "delete_value",  # DeleteValue
        "read_value",    # GetValue
        "write_value",   # SetValue
    ]
    fields = [
        # Registry Specific fields
        "data",
        "key",
        "data_type",
        "value",
        # Host fields
        "fqdn",
        "hostname",
        # Process/context fields for the event
        "exe",
        "image_path",
        "parent_image_path",
        "parent_exe",
        "ppid",
        "pid",
        "user"
    ]
    identifiers = [
        "pid",
        "key",
        "data",
        "data_type",
        "value"
    ]


class ThreadEvent(DataModelEvent):
    object_name = 'thread'
    actions = [
        "create",
        "remote_create",
        "suspend",
        "terminate"
    ]
    fields = [
        "fqdn",
        "hostname",
        "src_exe",
        "src_image_path",
        "src_parent_exe",
        "src_parent_image_path",
        "src_pid",
        "src_ppid",
        "src_tid",
        "stack_base",
        "stack_limit",
        "start_function",
        "start_address",
        "start_address_win32",
        "subprocess_tag",
        # "pid",
        # "tid",
        "target_exe",
        "target_image_path",
        "target_parent_exe",
        "target_parent_image_path",
        "target_pid",
        "target_ppid",
        "target_tid",
        "user",
        "user_stack_base",
        "user_stack_limit"
    ]
    identifiers = [
        "src_pid",
        "target_pid",
        "target_tid"
    ]


class UserEvent(DataModelEvent):
    object_name = 'user_session'
    actions = [
        "interactive",
        "local",
        "lock",
        "login",
        "logout",
        "privilege",
        "rdp",
        "reconnect",
        "remote",
        "unlock"
    ]
    fields = [
        "dest_ip",
        "dest_port",
        "hostname",
        "logon_id",
        "logon_type",
        "privileges",
        "src_ip",
        "src_port",
        "user"
    ]
