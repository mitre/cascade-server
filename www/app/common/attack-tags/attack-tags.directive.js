(function() {
  app = angular.module('cascade');
  app.directive('attackTags', function() {
    return {
      restrict: 'E',
      templateUrl: '/app/common/attack-tags/attack-tags.html',
      scope: {
        coverageList: '=',
        levels: '&'
      },
      controller: function($scope) {
        $scope.levels = {
          Low: 'danger',
          Moderate: 'warning',
          High: 'success',
          null: 'default',
          undefined: 'default'
        };
      }
    }
  });

})();
