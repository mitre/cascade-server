(function() {
  angular.module('cascade').directive('matrix', function() {
      return {
        restrict: 'E',
        templateUrl: '/app/common/attack-matrix/matrix.html',
        scope: {
          coverage: '=?', // list of {technique: technique, tactic: tactic}
          heatMap: '=?'
        },
        controller: function($scope, $http, AttackService) {
          var self = this;

          AttackService.init.then(function() {
            $scope.classes = {};
            _.each(AttackService.tactics, function(tactic) {
              $scope.classes[tactic._id] = {};
            });

            $scope.$watchGroup(['coverage', 'heatMap'], function() {
            _.each(AttackService.techniques, function(technique) {
              _.each(technique.tactics, function(tactic) {
                var classes = [];
                if ($scope.heatMap) {
                  classes.push($scope.heatMap[tactic._id][technique._id] ? 'selected' : 'faded');
                } else if ($scope.coverage) {
                  classes.push(($scope.coverage[tactic._id][technique._id] || 'no') + '-coverage');
                }
                $scope.classes[tactic._id][technique._id] = classes.join(' ');
              });
            });
          });
          });

          self.drawTable = function() {
            var table = [],
            maxRowLen = -1;

            AttackService.init.then(function(){
              $scope.tactics = AttackService.tactics;
              $scope.techniques = _.values(AttackService.techniques);
              var inverseMatrix = {}; // tacticId -> [techniqueA, techniqueB, techniqueC]

              // initialize the columns
              _.each(AttackService.tactics, function(tactic) {
                inverseMatrix[tactic._id] = [];
              })

              _.each(AttackService.techniques, function(technique) {
                _.each(technique.tactics, function(tactic) {
                  inverseMatrix[tactic._id].push(technique);
                })
              });

              var maxColumnLen = _.max(_.map(AttackService.tactics, function(tactic) { return inverseMatrix[tactic._id].length; }));
              var padding = {};

              _.each(AttackService.tactics, function(tactic) {
                padding[tactic._id] = maxColumnLen - inverseMatrix[tactic._id].length;
              });

              $scope.matrix = [];
              for (var i=0; i < maxColumnLen; i++) {
                var nextRow = [];
                _.each(AttackService.tactics, function(tactic) {
                  var technique = inverseMatrix[tactic._id][i];
                  if (technique) {
                    nextRow.push({tactic: tactic, technique: technique});
                  } else if (padding[tactic._id]) {
                    nextRow.push({}); //padding: padding[tactic._id]});
                    // padding[tactic._id] = 0;
                  }
                });
                $scope.matrix.push(nextRow);
              }
            });
          };

          self.drawTable();
        }
      }
  });
})();
