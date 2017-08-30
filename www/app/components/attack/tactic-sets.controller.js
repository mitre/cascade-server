(function() {
  var app = angular.module('cascade');

  app.controller('TacticSetsController', function($scope, $http, AttackService) {
      $scope.attack = AttackService;
      $scope.newTacticSet = [{}];

      function convertSet(tacticSet) {
        tacticSet.tactics = _.map(tacticSet.tactics, function(tacticId) {
          return AttackService.index.tactics[tacticId];
        });
        return tacticSet;
      }

      $http.get('/api/attack/tactic_sets').success(function(tacticSets) {
        AttackService.init.then(function() {
            $scope.tacticSets = _.map(tacticSets, convertSet);
        });
      });

      $scope.removeSet = function(tacticSet) {
        $http.delete('/api/attack/tactic_sets/' + tacticSet._id).success(function(status) {
          $scope.tacticSets.splice($scope.tacticSets.indexOf(tacticSet));
        });
      };

      $scope.addSet = function() {
        var data = {
            tactics: _.map($scope.newTacticSet, function(t) {
              return t._id;
            })
        };
        $http.post('/api/attack/tactic_sets', data).success(function (setId) {
          $scope.tacticSets.push({_id: setId, tactics: $scope.newTacticSet});
          $scope.newTacticSet = [{}];
        });
      };
    });
})();

