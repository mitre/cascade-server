(function() {
  var app = angular.module('cascade');

  app.controller('TuneAnalyticsController', function($scope, $http, AnalyticService, SessionService) {
      $scope.baselines = [];
      $scope.sessions = [];
      $scope.selected = {};
      $scope.timeData = {};

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

      $scope.submitTuning = function() {
        var start = {};
        var end = {};

        var data = {
          analytics: _.map(self.getCurrentConfig(), function(analyticConfig) {
            return {_id: analyticConfig.analytic};
          }),
          time: $scope.timeData
        };

        $http.post('/api/tuning', data).success(function(data){
          console.log('training posted successfully');
        });
      };

      $scope.setTimepicker = function(session) {
        $scope.timeData = {
          mode: "absolute",
          absolute: {
            start: new Date(session.range.start),
            end: new Date(session.range.end)
          }
        };
      }
      $scope.sessions = SessionService;

      $http.get('/api/tuning').success(function(baselines) {
        AnalyticService.init.then(function () {
          $scope.baselines = baselines;

          _.each($scope.baselines, function(baseline) {
            baseline.analytic = AnalyticService.index[baseline.analytic];
          });
        });
      });
  });
})();