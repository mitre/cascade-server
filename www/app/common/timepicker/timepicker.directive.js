(function() {
  app.directive('timepicker', function() {
    return {
      restrict: 'E',
      templateUrl: '/app/common/timepicker/timepicker.html',
      scope: {
        inputData: '='
      },
      controller: function($scope) {
        $scope.inputData = {};
        $scope.inputData.mode = 'absolute';
      }
    };
  });
})();