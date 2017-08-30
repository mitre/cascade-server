(function() {
  var app = angular.module('cascade')
  app.requires.push('ui.bootstrap.datetimepicker');

  app.directive('relativeTimepicker', function() {
    return {
      restrict: 'E',
      templateUrl: '/app/common/timepicker/relative-datetime-picker.html',
      scope: {
        range: '='
      },
      controller: function($scope) {
        $scope.$watchGroup(['days', 'hours', 'minutes'], function() {
            $scope.range = $scope.range || {};
            $scope.range.relative = $scope.range.relative || {};
            $scope.range.relative.end = 0;
            $scope.range.relative.start = -(((($scope.days||0) * 24 + ($scope.hours||0)) * 60 + ($scope.minutes||0)) * 60 );
        });
      }
    }
  });
})();