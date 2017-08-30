(function() {
  var app = angular.module('cascade');

  app.controller('TuneAnalyticController', function($scope, $http, $stateParams, AnalyticService) {
      $scope.analyticId = $stateParams.analyticId;
      $scope.transposed = true;

      function updateGraph(node, tooltip) {
        tooltip = tooltip || "";
        if (node.key) {
            node.tooltip = tooltip = tooltip + node.key + ':\t' + node.value + "\t(" + node.size + ")" + "\n";
        }
        if (node.children) {
            node.children.forEach(function(n) { updateGraph(n, tooltip)});
        }
      }

      function reload() {
        // initialize this from the analytic
        $http.get('/api/analytics/'+ $scope.analyticId + '/tuning').success(function(data){
          updateGraph(data.root);
          $scope.baseline = data;
        });
      }


      AnalyticService.init.then(function() {
        $scope.analytic = AnalyticService.index[$scope.analyticId];
        // load the list of all of the baselines
        // TODO: Pass this from the train_analytics scope if possible (one less API call)
        $http.get('/api/tuning').success(function(baselines) {
          $scope.baselines = _.map(baselines, function(baseline) {
            baseline.analytic = AnalyticService.index[baseline.analytic];
            return baseline;
          });
          reload();
        });
      });

      $scope.reset = function() {
        $http.post('/api/analytics/' + $scope.analyticId + '/tuning?reset').success(function(data) {
          updateGraph(data.root);
          data.analytic = $scope.analytic;
          $scope.baseline = data;
        });
      }

      $scope.optimize = function() {
        $http.post('/api/analytics/' + $scope.analyticId + '/tuning?optimize').success(function(data) {
          updateGraph(data.root);
          data.analytic = $scope.analytic;
          $scope.baseline = data;
        });
      }

      $scope.reTrain = function() {
        $http.post('/api/analytics/' + $scope.analyticId + '/tuning?retrain', {keys: $scope.baseline.keys}).success(function(data) {
          updateGraph(data.root);
          data.analytic = $scope.analytic;
          $scope.baseline = data;
        });
      }

      $scope.saveChanges = function() {
        function pruneTree(source) {
          if (source.disabled) {
            return {size: 0};
          }

          var node = {children: [], leaf: true, size: 0, key: source.key, value: source.value};
          var remaining_size = source.size;

          if ((source.children || []).length) {
            source.children.forEach(function(c) {
              var newChild = pruneTree(c);
              if (newChild && newChild.size) {
                remaining_size -= c.size;
                node.size += newChild.size;
                node.children.push(newChild);
                node.leaf = false;
                    // if the childNode is disabled, then
              } else {
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

        var newBaseline = {root: pruneTree($scope.baseline.root)/*, keys: $scope.baseline.keys */};
        $http.put('/api/analytics/' + $scope.analyticId + '/tuning', newBaseline).success(function(data) {
          updateGraph(data.root);
          data.analytic = $scope.analytic;
          $scope.baseline = data;
        });
      }
  });
})();