(function() {
    function getMessage(event) {
        var message = '';
        if (event.object_type === 'process' && event.action === 'create') {
            message = 'Execution of <strong>' + event.state.command_line + '</strong> (' + event.state.pid + ')';
            if (event.state.ppid) {
                message += '<br/> from parent ';
                if (event.state.parent_exe) {
                    message += '<i>' + event.state.parent_exe + '</i> ';
                }
                message += '(' + event.state.ppid + ')';
            }
        } else if (event.object_type == 'process' && event.action == 'terminate') {
            message = 'Termination of process ' + event.state.pid;
        } else if (event.object_type === 'process' && event.action === 'inject') {
            message = 'The process <strong>' + event.state.command_line + '</strong> (' + event.state.pid + ')<br/> was tainted as a result of thread injection';
        } else if (event.object_type === 'flow') {
            message = 'Connection to <strong>' + event.state.dest_ip + ':' + event.state.dest_port +
                          '</strong> via process ' + event.state.exe + ' (' + event.state.pid + ')';
        } else if (event.object_type === 'file') {
            message = 'File <strong>' + (event.state.file_path || event.state.file_name) + '</strong> ' + event.action;
            if (event.state.exe || event.state.pid) {
                message += ' by process <strong>' + event.state.exe +'</strong> (' + event.state.pid + ')';
            }
        } else if (event.object_type === 'thread' && event.action === 'remote_create') {
            message = 'The process ' + event.state.src_exe + ' (' + event.state.src_pid + ') <strong>injected</strong> into process <strong><br/>' + (event.state.target_path || event.state.target_exe) + '</strong> (' + event.state.target_pid + ')';
            if (event.state.start_function && event.state.start_function !== 'FAIL') {
                message += '<br/> at the function <strong>' + event.state.start_function + '</strong>';
            }
        }

        return message;
    }

  var app = angular.module('cascade');
  app.requires.push('ngSanitize');

  app.directive('eventTimeline', function() {
    return {
      restrict: 'E',
      templateUrl: '/app/common/event-timeline/event-timeline.html',
      scope: {
        events: '='
      },
      controllerAs: 'ctrl',
      controller: function($scope) {
         var self = this;

        $scope.columns = [
            'time',
            'hostname',
            'user',
            'object_type',
            'action',
            'message',
            'techniques',
            'tactics'
        ];

        $scope.headers = {
           time: 'Time', hostname: 'Host', user: 'User', object_type: 'Event Type', action: 'Action',
           message: 'Event', techniques: 'ATT&CK Technique', tactics: 'ATT&CK Tactics'
        };

        $scope.rows = []
        self.showAll = false;
        $scope.parsedEvents = [];

        function updateEvents() {
          $scope.rows = _.filter($scope.parsedEvents, function(event){
            return self.showAll || (event.techniques && event.techniques.length) || (event.tactics && event.tactics.length);
          });//.map(eventToRow)
        }

        $scope.$watch('events', function() {
            $scope.parsedEvents = _.map($scope.events, function(event) {
                return {
                    time: event.time.replace("T", " ").replace("+00:00", "Z"),
                    hostname: event.state.hostname,
                    user: event.state.user,
                    object_type: event.object_type,
                    action: event.action,
                    message: getMessage(event),
                    techniques: (event.attack || {}).techniques,
                    tactics: (event.attack || {}).tactics
                };
            });
            updateEvents();
        });

        /**
         * Controller function to show/hide rows
         * with/without ATT&CK mappings.
         * TODO: could this be better?
         */
        self.toggleEvents = function() {
          self.showAll = !self.showAll;
          updateEvents();
        }
      }
    }
  });
})();