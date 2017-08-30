(function () {
    angular.module('cascade').directive('progressBar', function() {

      return {
        restrict: 'EA',
        templateUrl: '/app/common/progress-bar/progress-bar.html',
        scope: {
            total: '=',
            fail: '=?',
            success: '=?',
            pending: '=?',
        },
        controller: function($scope, $http) {
          $scope.percent = {
            fail: 0,
            success: 0,
            pending: 0
          }
          $scope.$watch(function() {
            if ($scope.total) {
              _.each(['fail', 'success', 'pending'], function(key) {
                $scope.percent[key] = Math.round($scope[key] * 100 / ($scope.total || 1));
              })
            }
          });
        }
      }
    });
})();