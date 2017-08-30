(function() {
  var app = angular.module('cascade');

  app.controller('RunAnalyticsController', function($scope, $http, $state, $stateParams, SessionService, AnalyticService) {
      var self = this;
      self.sessionId = $stateParams.sessionId;
      self.baselines = {};
      $http.get('/api/tuning').success(function (baselines) {
        self.baselines = _.indexBy(baselines, 'analytic');
      });

      self.sessions = SessionService;


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


      $scope.runAnalytics = function() {
        // TODO: figure out a better way to do this other than sharing a function across the scope. set $watch instead?
        var analytics = []
        var missing = [];
        // check analytics that have not been tuned yets
        _.each(self.getCurrentConfig(), function(analyticConfig) {
            console.log(analyticConfig);
            var analytic = AnalyticService.index[analyticConfig.analytic];
            console.log(analytic);
            if (analyticConfig.mode == 'first-pass' && !self.baselines[analytic._id]) {
                missing.push(analytic.name);
            }
            analytics.push({_id: analytic._id, mode: analyticConfig.mode})
        })

        var warningMessage = ("WARNING! The following analytics have not been tuned " +
                              "and may result in significant volume, causing slowdown, etc.\n\n" +
                              missing.join("\n") + "\n\n" +
                              "Press OK to continue running analytics."
                              );

        console.log(missing.length);
        if (missing.length === 0 || confirm(warningMessage)) {
            $http.post('/api/sessions/' + self.sessionId + '/automate', {analytics: analytics}).success(function(data) {
              $state.go('eventMap', {sessionId: self.sessionId});
            });
        }
      }
    });
})();

