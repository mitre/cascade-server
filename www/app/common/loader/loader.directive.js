(function() {
  var app = angular.module('cascade');

  app.directive('loader', function() {
    return {
      restrict: 'E',
      templateUrl: '/app/common/loader/loader.html',
      scope: {
        size: "=?"
      }
    }
  });
})();