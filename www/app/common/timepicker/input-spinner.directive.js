(function() {
  var app = angular.module('cascade');

  app.directive('inputSpinner', function() {
    return {
      restrict: 'E',
      templateUrl: '/app/common/timepicker/input-spinner.html',
      scope: {
        min: '=?',
        max: '=?',
        inc: '=?',
        value: '='
      },
      controller: function($scope) {
        $scope.increment = function(up) {

          $scope.value = parseFloat($scope.value || 0);
          var maxValue = ($scope.max == 0) ? 0 : ($scope.max || Infinity);
          var minValue = ($scope.min == 0) ? 0 : ($scope.min || -Infinity);
          var delta = (up ? 1 : -1) * ($scope.inc || 1);

          $scope.value = Math.max(minValue, Math.min(maxValue, $scope.value + delta));
        }
      }
    }
  });

})();