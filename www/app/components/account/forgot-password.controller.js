(function() {
  var app = angular.module('cascade');

  app.controller('ForgotPasswordController', function($http, $rootScope, $scope, $cookies, $state, $stateParams, SessionService) {
      // hidden parameter username defined in route
      $scope.email = $stateParams.email;
      //$scope.password = "Password";
      $scope.submitted = false;

      $scope.submit = function() {
        // TODO: check input
        $http.post('/api/login?action=forgot_password', {email: $scope.email}).success(function(data) {
            $scope.submitted = true;
        })
        .catch(function(err){
            if (err.status == 401) {
              $scope.error = "Invalid login credentials. Try again."
            }
        });
      }
    });
})();

