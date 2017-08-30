(function() {
  var app = angular.module('cascade');

  app.controller('DataModelController', function($http, $stateParams, $scope, $rootScope) {
    $scope.glyphs = {
      api: 'glyphicon-sort-by-attributes-alt',
      registry: 'glyphicon-tree-deciduous',
      thread: 'glyphicon-fire',
      file: 'glyphicon-file',
      flow: 'glyphicon-transfer',
      module: 'glyphicon-list',
      user_session: 'glyphicon-user',
      driver: 'glyphicon-road',
      process: 'glyphicon-leaf'
    };

    return $http.get('/api/data_model').success(function(data_model) {
      $scope.objects = data_model.objects;
      $scope.pivots = data_model.pivots;
    });
  });
})();