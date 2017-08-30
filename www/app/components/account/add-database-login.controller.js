(function() {
  var app = angular.module('cascade');

  app.controller('AddDatabaseController', function($http, $scope, $state) {
      $scope.selection = 0;

      $scope.submit = function() {
        args = {
          database: $scope.selection,
          username: $scope.username,
          password: $scope.password,
        }

        $http.post('/api/user/databases?action=add', args).then(function(data) {
          $state.go('account');
        }, function(error) {
          alert('Login Error.');
        });
      }

      var store = this;
      store.databases = []

      $http.get('/api/databases').success(function(data) {
        store.databases = data;
        $scope.selection = data[0]._id;
      });
    });
})();