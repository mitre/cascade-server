(function() {
  var app = angular.module('cascade');

  app.controller('AlertGraphController', function($scope, $http, $stateParams, AnalyticService) {
    self.sessionId = $stateParams.sessionId;
    $scope.sessionId = self.sessionId;

    $http.get('/api/sessions/' + $stateParams.sessionId + '/graphs/alerts').success(function(data) {
      AnalyticService.init.then(function() {
        $scope.nodes = _.map(data.nodes, function(result) {
            result.analytic = AnalyticService.index[result.analytic]
            return {
                title: "Alert",
                subtitle: result.analytic.name,
                group: "analytic_result",
                family: "analytic_result",
                item: result,
                id: result._id
            };
        });
        var resultIndex = _.indexBy($scope.nodes, 'id');

        $scope.links = _.map(data.edges, function(e) {
          var sourceId = e[0],
              targetId = e[1];
          return {source: resultIndex[sourceId], target: resultIndex[targetId], value: 1};
        });
      });
    });
  });
})();