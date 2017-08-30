(function() {
  var app = angular.module('cascade');

  app.controller('TechniqueGraphController', function($scope, $rootScope, $stateParams, $http, AnalyticService, AttackService) {
      self.sessionId = $stateParams.sessionId;
      $scope.sessionId = self.sessionId;

      $scope.nodes = [];
      $scope.links = [];

      // This is boilerplate at this point...
      $http.get('/api/sessions/' + $stateParams.sessionId + '/graphs/technique').success(function(data) {
        AttackService.init.then(function() {
            AnalyticService.init.then(function() {
                $scope.nodes = data.nodes.map(function(node) {
                    var group = node.group;
                    var attackItem;
                    if (node.group === 'technique') {
                        attackItem = node.technique = AttackService.index.techniques[node.technique];
                    } else if (node.group === 'tactic') {
                        attackItem = node.tactic = AttackService.index.tactics[node.tactic];
                    } else {
                        return { id: node._id || node.id, group: 'event', family: null};
                    }

                    return {
                        family: group,
                        group: group,
                        title: group == 'tactic' ? attackItem.name.toUpperCase() : attackItem.name,
                        subtitle: 'ATT&CK ' + group[0].toUpperCase() + group.slice(1),
                        item: node,
                        id: node._id || node.id,
                    }
                });

                var nodeIndex = _.indexBy($scope.nodes, 'id');

                $scope.links = _.map(data.edges, function(e) {
                  var sourceId = e[0],
                      targetId = e[1];
                  return {source: nodeIndex[sourceId], target: nodeIndex[targetId], value: 1};
                });
            });
        });
      });
  });
})();