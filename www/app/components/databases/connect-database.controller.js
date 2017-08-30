(function() {
  var app = angular.module('cascade');

  app.controller('ConnectDatabaseController', function($http, $scope, $state) {
      var self = this;

      $scope.dbInfo = {name: null, _cls: null};
      $scope.dbFields = {};

      var databasePromise = $http.get('/api/schemas/databases').success(function(dbSchemas) {
        $scope.dbSchemas = dbSchemas;
        $scope.schemaFields = {};
        
        _.each(dbSchemas, function(dbs) { 
          $scope.schemaFields[dbs._cls] = dbs.fields;
        });

        $scope.$watch('dbInfo._cls', function() {
          $scope.dbFields = {};
          // update defaults
          _.each($scope.schemaFields[$scope.dbInfo._cls], function(v,k) {
            if (v.default !== null) {
              $scope.dbFields[k] = v.default;
            }
          });
        })


      });

      self.submit = function() {
        var dbInfo = _.extend({}, $scope.dbInfo, $scope.dbFields);
        $http.post('/api/databases', dbInfo).success(function(data) {
          console.log(data);
          $state.go('manageExternalDatabases');

        });



      }

    });
})();