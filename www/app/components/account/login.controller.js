(function() {
  var app = angular.module('cascade');

  app.controller('LoginController', function($http, $rootScope, $scope, $cookies, $state, $stateParams, SessionService) {
      // hidden parameter username defined in route
      $scope.username = $stateParams.username;
      //$scope.password = "Password";
      $scope.$watch('password', function() {
        if ($scope.error) {
          $scope.error = null;
        }

      })

      $scope.submit = function() {
        // TODO: check input
        $http.post('/api/login', {user: $scope.username, password: $scope.password}).success(function(data) {
          $cookies.put('user-token', data.api_token);
          $rootScope.user = data; //{username: data.username, full_name: data.fullname, email: data.email}
          SessionService.refresh();
          $state.go('index');
          console.log("login success");
        })
        .catch(function(err){
            if (err.status == 401) {
              $scope.error = "Invalid login credentials. Try again."
            }
        });
      }
    });
})();

