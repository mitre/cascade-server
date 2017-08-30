(function() {
  var app = angular.module('cascade');

  app.controller('EventMapController', function($http, $stateParams, $scope, AnalyticService) {
      var self = this;
      self.sessionId = $stateParams.sessionId;
      $scope.sessionId = self.sessionId;

      // Map events to indicies in array for D3
      // Also generate text for each of the nodes
      var x = 0;
      var events = [];
      var connections = {};
      $http.get('/api/sessions/' + self.sessionId + '/events').success(function(events) {
        $scope.events = events;
      });

      $http.get('/api/sessions/' + self.sessionId + '/results').success(function(results) {
        AnalyticService.init.then(function() {
            _.each(results, function(result) { result.analytic = AnalyticService.index[result.analytic]; });
            $scope.results = results;
        });
      });
    });
})();