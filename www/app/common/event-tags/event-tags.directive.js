(function() {
  var app = angular.module('cascade');

  app.directive('eventTags', function() {
    return {
      restrict: 'E',
      templateUrl: '/app/common/event-tags/event-tags.html',
      scope: {
        mappedEvents: '=',
        labels: '&'
      },
      controller: function($scope) {

        $scope.labels = {
          process:'default', flow:'default', registry: 'default', user_session:'default', file: 'default', thread: 'default'
        };
      }
    }
  });
})();