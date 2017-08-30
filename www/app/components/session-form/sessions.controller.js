(function() {
  var app = angular.module('cascade');

  app.controller('CreateSessionController', function($state, $rootScope, $scope, $http) {
      $scope.time = {};
      $scope.session_name = "";
      $scope.mode = 'absolute';

      $scope.submitSession = function() {

        $http.post('/api/sessions', {name: $scope.session_name, range: $scope.time}).success(function(sessionId) {
            // the session service will take care of updating, etc
            $state.go('eventMap', {sessionId: sessionId});
        });
      }
    });
})();

