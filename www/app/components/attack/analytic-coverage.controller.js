(function() {
  var app = angular.module('cascade');

  app.controller('AnalyticCoverageController', function($http, $stateParams, $scope, $rootScope, AnalyticService, AttackService) {
      AnalyticService.init.then(function() {
        $scope.analytics = AnalyticService.analytics;
        AttackService.init.then(function() {
          $scope.coverage = AnalyticService.attackCoverage;
        });
      });
    });
})();