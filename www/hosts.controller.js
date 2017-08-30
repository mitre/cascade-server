(function() {
  var app = angular.module('cascade');

  app.controller('HostGraphController', function($scope, $http, $stateParams, $rootScope) {
      $scope.links = [];
      $scope.nodes = [];

      $http.get('/api/sessions/' + $stateParams.sessionId + '/clusters/hosts').success(function(data) {
        var links = [];

        data.forEach(function(node) {
          node.title = node.host.hostname
          node.subtitle = node.host.fqdn.split('.').slice(1).join('.');
          node.group = 'host';
          node.tooltip = "fqdn: " + node.host.fqdn + "\nhostname: " + node.host.hostname + "\nusers: " + node.host.users + "\ninterfaces: " + node.host.interfaces + "\nleases:" + node.host.leases;

          node.links.forEach(function(link) {
            links.push({source : node, target : data[link], value : 1})
          })
        });
        $scope.nodes = data;
        $scope.links = links;
      });
  });
})();