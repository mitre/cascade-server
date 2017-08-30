(function () {
    angular.module('cascade').directive('jobProgressBar', function() {

      return {
        restrict: 'EA',
        template: '<div progress-bar total="jobs.total" fail="jobs.failure" success="jobs.success" pending="jobs.started + jobs.ready + jobs.created + jobs.dispatched"></div>',
        scope: {
            filter: '='
        },
        controller: function($scope, $http) {
          $scope.percent = {
            fail: 0,
            success: 0,
            pending: 0
          }

          $scope.jobs = {};
          function updateJobs() {
            $http.get('/api/jobs?format=summary', {params: $scope.filter}).success(function(summary) {
            // {total: summary.total, fail: summary.failure, success: summary.success, pending: summary.started};
              $scope.jobs = summary;
            })
          }

          $scope.$watch('sessionId', function() {
            if ($scope.sessionId) {
                updateJobs();
            }
          })

          $scope.jobTimer = setInterval(updateJobs, 10000);
          setTimeout(updateJobs, 1000);

          $scope.$on('$destroy', function() {

            if ($scope.jobTimer) {
              clearInterval($scope.jobTimer);
              $scope.jobTimer = null;
            }
          });

          $scope.$watch(function() {
            if ($scope.total) {
              _.each(['fail', 'success', 'pending'], function(key) {
                $scope.percent[key] = Math.round($scope[key] * 100 / $scope.total);
              })
            }
          });
        }
      }
    });
})();