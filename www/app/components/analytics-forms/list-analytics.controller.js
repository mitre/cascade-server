(function() {
  var app = angular.module('cascade');

  app.controller('ListAnalyticsController', function($http, $stateParams, $scope, $rootScope, AnalyticService) {
    $scope.platforms = {};
    $scope.queries = {};
    $scope.format = 'Data Model Query Language';

    $http.get('/api/query/languages').success(function(languages) {
      $scope.formats = languages;
    });

    function updateQueries(format, analytics) {
      $scope.queries[format] = $scope.queries[format] || {};
      _.each(analytics, function(analytic) {
        $scope.queries[format][analytic._id] = (format === 'Data Model AST' || format === 'Mongo') ? JSON.stringify(analytic.query, null, 2) : analytic.query;
      });
    }

    AnalyticService.init.then(function() {
      $scope.analytics = AnalyticService.analytics;
      $scope.platforms = {};
      _.each(AnalyticService.analytics, function(analytic) {
        $scope.platforms[analytic.platform] = true;
      });
    });

    $scope.$watch('format', function() {
      var format = $scope.format;
      if (! $scope.queries[format]) {
        $http.get('/api/analytics?format=' + format).success(function(analytics) {
          updateQueries(format, analytics);
        });
      }
    });
  });
})();