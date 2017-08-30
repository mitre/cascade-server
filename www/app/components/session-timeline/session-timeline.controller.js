(function() {

  var app = angular.module('cascade');

  app.controller('SessionTimelineController', function($scope, $http, $stateParams, AttackService) {

      $http.get('/api/sessions/' + $stateParams.sessionId + '/events').success(function(eventData) {
        _.each(eventData, function(e) {
            e.attack = {tactics: [], techniques: []}
        });
        $scope.events = eventData;

        $http.get('/api/sessions/' + $stateParams.sessionId + '/attack_timeline').success(function(attackTimeline) {
          AttackService.init.then(function() {
            var eventLookup = _.indexBy(eventData, '_id');

            _.each(attackTimeline, function(attackEvent) {
              var techniqueName = AttackService.index.techniques[attackEvent.technique].name;
              var tactics = _.map(attackEvent.tactics, function(tacticId) {
                return AttackService.index.tactics[tacticId].name;
              });

              var event = eventLookup[attackEvent.event_id];
              if (event) {

                if (event.attack.techniques.indexOf(techniqueName) == -1) {
                  event.attack.techniques.push(techniqueName);
                }

                _.each(tactics, function(tactic) {
                  if (event.attack.tactics.indexOf(tactic) == -1) {
                    event.attack.tactics.push(tactic);
                  }
                });
              }
            });
            // recreate this, forcing the directive to update
            $scope.events = _.map(eventData, x => x);
          });
        });
      });
    });
})();