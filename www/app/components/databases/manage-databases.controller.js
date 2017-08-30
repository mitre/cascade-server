(function() {
  var app = angular.module('cascade');

  app.controller('ManageDatabasesController', function($http, $cookies, $scope, $state) {
    	$http.get('/api/databases').success(function(databases) {
    		$scope.databases = databases;
    		console.log(databases);
    	});

		$http.get('/api/schemas/databases').success(function(schemas) {
			$scope.schemas = _.indexBy(schemas, '_cls');
		});

    });
})();