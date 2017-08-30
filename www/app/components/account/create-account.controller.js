(function() {
  var app = angular.module('cascade');

  app.controller('CreateAccountController', function($scope, $http, $state, $cookies, $rootScope){
      var self = this;
      self.login = function(){

        var token = $cookies.get("user-token");

        if (token){
          $http.post("/api/login", {api_token: token}).success(function(data) {
            $rootScope.user = data;
            $state.go('index');
          });
        }
      };

      $scope.$watchGroup(['new_user.password', 'confirmPassword'],  function() {
        if ($scope.new_user.password && $scope.confirmPassword && ($scope.new_user.password == $scope.confirmPassword)) {
          $scope.error = "";
        }
      });

      /**
       * This function is invoked when the Create Account form is
       * submitted. We may want to add some sort of client side
       * validation before submitting to the API.
       */
       $scope.createAccount = function(){
        if ($scope.new_user.password !== $scope.confirmPassword) {
          $scope.error = "Passwords do not match";
          return;
        }

        if($scope.accountForm.$valid){
          $http.post('/api/user', $scope.new_user, {})
          .success(function(data){
            self.login();
          })
          .catch(function(err){
            if (err.status == 403) {
              $scope.error = "Account creation disabled. Please contact your administrator."
            } else if (err.status == 400)
                if (err.data.violation) {
                    $scope.error = "Password does not match complexity requirements:";
                    $scope.passwordPolicy = err.data.violation.rules;
            } else {
                $scope.error = err.data.message || ("Server Error " + error.status + " when creating account");

            }
            console.log('error!', err);
                      // empty for now
                      // may want to display an error in the future
                    });
        }
      };
    });
})();

