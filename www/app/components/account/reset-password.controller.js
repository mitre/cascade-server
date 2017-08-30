(function() {
  var app = angular.module('cascade');

  app.controller('ResetPasswordController', function($stateParams, $http, $scope, $state) {
      var self = this;
      self.resetToken = $stateParams.token;
      $scope.username = $stateParams.username;
      console.log($stateParams);

      $scope.$watchGroup(['password', 'confirmPassword'],  function() {
        if ($scope.password && $scope.confirmPassword && ($scope.password == $scope.confirmPassword)) {
          $scope.error = "";
        }
      });

      self.submit = function() {
        if ($scope.password !== $scope.confirmPassword) {
          $scope.error = "Passwords do not match";
          return;
        }

        $http.post('/api/login?action=reset_password', {token: self.resetToken, password: $scope.password}).success(function(user) {
          $state.go('login', {user: user.username});
        }).catch(function(err) {
            if (err.status == 400 && err.data.violation) {
                    $scope.error = "Password does not match complexity requirements:";
                    $scope.passwordPolicy = err.data.rules;
            } else {
                $scope.error = "Server Error " + error.status + " when resetting password";
            }
        });
    }
    });
})();