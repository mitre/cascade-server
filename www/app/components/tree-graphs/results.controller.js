(function() {
  var app = angular.module('cascade');

  app.controller('ResultTreeController', function($scope, $http, $stateParams, AnalyticService) {
    self.sessionId = $stateParams.sessionId;
    $scope.sessionId = self.sessionId;

      $scope.treeIndex = {};
      $scope.transposed = false;

      $scope.$watch('selectedAnalytic', function() {
        if ($scope.selectedAnalytic) {
          $scope.resultTree = $scope.treeIndex[$scope.selectedAnalytic._id];
        }
      });

      $scope.reCluster = function() {
        var analyticId = $scope.selectedAnalytic._id;
        var fieldList = _.map(_.where($scope.resultTree.keys, {status: true}), function(k) { return k.name; });

        $http.get('/api/sessions/' + $stateParams.sessionId +   '/results/' + analyticId, {params: {format: 'tree', key: fieldList}}).success(function(data) {
          $scope.treeIndex[analyticId] = data;
          if ($scope.selectedAnalytic._id == analyticId) {
            $scope.resultTree = data;
          }
        });
      }

      $scope.saveChanges = function() {
        function pruneTree(source) {
          if (source.disabled) {
            return null;
          }

          var node = {children: [], leaf: true, size: 0, key: source.key, value: source.value};
          var remaining_size = source.size;

          if ((source.children || []).length) {
            source.children.forEach(function(c) {
              var newChild = pruneTree(c);
              if (newChild) {
                remaining_size -= c.size;
                node.size += newChild.size;
                node.children.push(newChild);
                node.leaf = false;
                      // if the childNode is disabled, then
              } else if (c.disabled) {
                remaining_size -= c.size;
              }
            });
          }
          /*
          if ((source._children || []).length) {
              source._children.forEach(function(c) {
                remaining_size -= c.size;
              });
          }*/
          node.size += remaining_size;
          return node;
        }

        var new_whitelist = {root: pruneTree($scope.whitelist.root)/*, keys: $scope.whitelist.keys */};
        $http.put('/api/analytics/' + $scope.whitelist.analytic.id + '/training', new_whitelist).success(function(data) {

          $scope.whitelist = data;
          // dereference this from the scope
          AnalyticService.init.then(function() {
            $scope.whitelist.analytic = AnalyticService.index[$scope.whitelist.analytic];
          });
        });
      }

      // initialize this from the analytic
      $http.get('/api/sessions/' + $stateParams.sessionId + '/results', {params: {format: 'tree'}}).success(function(data){
        AnalyticService.init.then(function() {
          // $scope.resultTree = data;
          $scope.treeIndex = _.indexBy(data, 'analytic');
          $scope.triggeredAnalytics = _.map(data, function(analytic_tree) {
            return analytic_tree.analytic = AnalyticService.index[analytic_tree.analytic];
          });
        });
      });
  });
})();