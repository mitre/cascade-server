(function() {
  var app = angular.module('cascade');

  app.directive('navbar', function() {
    return {
      restrict: 'E',
      templateUrl: '/app/common/navbar/nav.html',
      controller: function($http, $state, $rootScope, $cookies, $scope, $window, SessionService) {

        var self = this;
        $scope.sessionFile = null;
        SessionService.init.then(function() {
            $scope.sessions = SessionService;
        });

        $scope.removeSession = function() {
          $http.delete('/api/sessions/' + SessionService.currentId).success(function() {
            SessionService.refresh();
            // use jQuery to close the modals
            $('.modal').modal('hide');
            $state.go('index');
          });
        };

        /**
         * Helper function to initialize a new session object
         *
         */
        $scope.buildClone = function(){
          $scope.newSession = {
            name: SessionService.current.name + ' - Clone'
          }
        };

        $scope.resetUploadModal = function() {
          $scope.message = null;
        }

        $scope.uploadSession = function(file) {
          var fd = new FormData();
          fd.append('file', file);

          $http.post('/api/utils/upload', fd, {
            transformRequest: angular.identity,
            headers: {'Content-Type': undefined}}).success(function(data) {
              $scope.message = data.message;
            });
          }

        /**
         * Use the API to clone the current session and redirect the browser
         * to the newly cloned session.
         */
        $scope.cloneSession = function(){
          $http.post('/api/sessions?clone=' + SessionService.currentId, $scope.newSession).success(function(sessionId){
            // use jQuery to close the modals
            $('.modal').modal('hide');
            $state.go($state.current.name, {sessionId: sessionId});
          });
        };

        /**
         * Use the API to reset the current session
         */
         $scope.resetSession = function(){
          $http.post('/api/sessions/' + SessionService.currentId + '?reset=true').success(function(){
            // refresh the view
            $('.modal').modal('hide');
            $state.go($state.current.name, {sessionId: sessionId});
          });
        };

        /**
         * Use the API to refresh the current session
         */
         $scope.refreshSession = function(){
          $http.post('/api/sessions/' + SessionService.currentId + '?refresh=true').success(function(){
            $state.reload();
          });
        };

        /**
         * Logs the user out. Removes their user-token cookie and redirects
         * the user the front page.
         */
        $scope.logout = function() {
          $cookies.remove('user-token');
          $rootScope.user = undefined;
          $state.reload('index');
          $state.go('index');
        }
      }
    };
  });
})();