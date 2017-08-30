(function() {
  var app = angular.module('cascade');

  app.controller('HostGraphController', function($scope, $http, $stateParams, $rootScope) {
      self.sessionId = $stateParams.sessionId;
      $scope.sessionId = self.sessionId;

      $scope.links = [];
      $scope.nodes = [];
      $http.get('/api/sessions/' + $stateParams.sessionId + '/clusters/hosts').success(function(data) {
        var links = [];
        data.forEach(function(node) {
          var host = node.host;
          node.title = host.hostname
          node.subtitle = host.fqdn.split('.').slice(1).join('.');
          node.group = 'host';
          node.tooltip = "fqdn: " + host.fqdn + "\nhostname: " + host.hostname + "\nusers: " + host.users + "\ninterfaces: " + host.interfaces + "\nleases:" + host.leases;
          node.links.forEach(function(link) {
             if (data[link]) {
                links.push({source : node, target : data[link], value : 1})
            }
          })
        });
        $scope.nodes = data;
        $scope.links = links;
      });
    });
})();