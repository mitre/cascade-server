(function() {
  var app = angular.module('cascade')

  app.directive('analyticConfigurationButtons', function() {
    return {
      restrict: 'E',
      templateUrl: '/app/components/analytics-forms/configuration-buttons.html',
      scope: {
        analytics: '=',
        platforms: '=',
        configuration: '=?',
        configurations: '=?',
        activeConfig: '=?',
        disableModes: '=?'
      },
      controllerAs: 'buttonCtrl',
      controller: function($scope, $http, AnalyticService) {
        var self = this;

        self.modes = {'first-pass': 'First Pass',
                      'second-pass': 'Second-Pass',
                      'identify-only': 'Identify Only',
                      'identify-only-no-baseline': 'Identify Only (Skip Baseline)'
                     };

        // set the initial configuration state to what's originally defined in the analytics
        AnalyticService.init.then(function() {
          self.defaultConfig = {name: "Default", analytics: []};

          _.each(AnalyticService.analytics, function(analytic) {
              if (analytic.enabled) {
                self.defaultConfig.analytics.push({analytic: analytic._id, mode: analytic.mode});
              }
          });

          self.selectConfiguration(self.defaultConfig);
        });

        $http.get("/api/configurations/analytics").success(function(configs) {
            $scope.configurations = configs;
        });

        self.selectConfiguration = function(config) {
          // takes a list of analytic configurations [{analytic: id, mode: 'first-pass'}, {...}]
          // and updates the active config to {id: {mode: '...'}, ...}
          // finally setting it to the active configuration
          var newConfiguration = {};

          if (config === self.defaultConfig) {
            $scope.activeConfig = null;
          } else {
            $scope.activeConfig = config;
          }

          AnalyticService.init.then(function() {
              // initialize the mapping first, even to empty things, so data binding doesn't break
              _.each(AnalyticService.analytics, function(analytic) {
                  newConfiguration[analytic._id] = {};
              });

              _.each(config.analytics, function(analyticConfig) {
                  newConfiguration[analyticConfig.analytic] = {mode: analyticConfig.mode, selected: true};
              });
              $scope.configuration = newConfiguration;
          });
        }


        self.setModes = function(runMode) {
          _.each(AnalyticService.analytics, function(analytic) {
            $scope.configuration[analytic._id].mode = runMode;
          });
        }

        self.selectAll = function() {
          _.each(AnalyticService.analytics, function(analytic) {
            $scope.configuration[analytic._id].selected = $scope.platforms[analytic.platform];
          });
        }

        self.clearAll = function() {

          _.each(AnalyticService.analytics, function(analytic) {
            $scope.configuration[analytic._id].selected = false;
          });
        };

        self.undoChanges = function() {
          self.activeConfig = null;
          self.selectConfiguration(self.defaultConfig);
        }
      }
    }
  });


})();