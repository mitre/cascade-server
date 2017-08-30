(function() {
  var app = angular.module('cascade');

  app.controller('ConfigureAnalyticsController', function($scope, $http, $state, AnalyticService) {
    var self = this;

    self.getCurrentConfig = function() {
        // crawls the current config of analytics {id: {mode: 'first-pass' | 'second-pass', selected: true|false}, ...}
        // and turns it into [ {analytic: id, mode: 'first-pass'}, ... ]
        var config = [];
        _.each(AnalyticService.analytics, function(analytic) {
            var analyticConfig = $scope.configuration[analytic._id];
            if (analyticConfig && analyticConfig.selected) {
                config.push({analytic: analytic._id, mode: analyticConfig.mode});
            }
        });
        return config;
    }

    self.update = function() {
        var configId = $scope.activeConfig._id;
        // server only implements a patch
        $http.put("/api/configurations/analytics/" + configId, {analytics: self.getCurrentConfig()})
             .success(function(configId) {
                $(".modal").modal("hide");
                $http.get("/api/configurations/analytics/" + configId).success(function(newConfig) {
                    $scope.configurations.push(newConfig);
                });
             });

      var newConfiguration = {name: $scope.configName, analytics: self.getCurrentConfig()};
    };

    self.removeConfig = function(configId) {
        $http.delete("/api/configurations/analytics/" + configId).success(function() {
            // force the whole state to reload all configurations
            $scope.activeConfig = null;
            $state.reload();
        });
    }

    self.saveConfig = function() {
        $http.post("/api/configurations/analytics", {name: $scope.configName, analytics: self.getCurrentConfig()})
             .success(function(configId) {
                $(".modal").modal("hide");
                $http.get("/api/configurations/analytics/" + configId).success(function(newConfig) {
                    $scope.configurations.push(newConfig);
                    $scope.activeConfig = newConfig;
                });
        });
    };

  });
})();

