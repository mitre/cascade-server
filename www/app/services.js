(function() {
  var app = angular.module('cascade');

  app.service('SessionService', function($http, $q) {
    // better practice than $rootScope
    var self = this;


    self.deferred = $q.defer();
    self.init = self.deferred.promise;

    self.index = {};
    self.current = {};
    self.currentId = null;
    self.list = [];

    self.refresh = function (sessionId) {
        if (sessionId) {
            $http.get('/api/sessions/' + sessionId).success(function(session) {
                if (!self.index[sessionId]) {
                    self.list.push(session);
                }

                self.index[sessionId] = session;
                if (sessionId == self.currentId) {
                    if (self.currentId) {
                        self.current = self.index[self.currentId];
                    }
                    // if the session disappears clear the currentId
                    if (!self.current) {
                        self.currentId = null;
                    }
                }
            });
        } else {
            $http.get('/api/sessions').success(function(sessions) {
                self.list = sessions;
                self.index = _.indexBy(sessions, '_id');
                if (self.currentId) {
                    self.current = self.index[self.currentId];
                }
                // if the session disappears clear the currentId
                if (!self.current) {
                    self.currentId = null;
                }

                self.deferred.resolve();
            }).catch(function(errorResponse) {
                if (errorResponse.status == 401) {
                    console.log("Error " + errorResponse.status + " when retrieving sessions");
                }
            });
        }

    }

    self.refresh();

    // update the sessions every 60 seconds
    self.updateTimer = setInterval(self.refresh, 10 * 60 * 1000);

    self.activate = function(sessionId) {
        self.currentId = sessionId;
        self.current = self.index[sessionId];

        if (!self.current) {
            self.refresh(sessionId); // will cause self.current to update when ajax finishes
        }
    }
  });

  app.service('AttackService', function($http, $q){
    // better practice than $rootScope
    var self = this;


    self.deferred = $q.defer();
    self.init = self.deferred.promise;


    $http.get('/api/attack')
    .success(function(attack){
      self.tactics = _.sortBy(attack.tactics, function(tactic) { return tactic.order; });
      self.techniques = _.sortBy(attack.techniques, function(technique) { return technique.name; }); 

      self.index = {
        tactics: _.indexBy(attack.tactics, '_id'),
        techniques: _.indexBy(attack.techniques, '_id')
      };

      // dereference the techniques
      _.each(attack.techniques, function(technique) {
        technique.tactics = _.map(technique.tactics, function(tacticId) { return self.index.tactics[tacticId]; });
      });

      self.deferred.resolve();
    });
  });

  app.service('AnalyticService', function($http, AttackService, $q){
    // better practice than $rootScope
    var self = this;
    // self.analytics = []
    // self.index = {analytic._id : analytic, ...}

    function dereferenceCoverage(coverage) {
      // dereference ATT&CK techniques, unless this has already happened
      return _.map(coverage, function(techniqueCoverage) {
        var coverageLevel = techniqueCoverage.level;
        return {
          level: coverageLevel,
          technique: techniqueCoverage.technique._id ? techniqueCoverage.technique : AttackService.index.techniques[techniqueCoverage.technique],
          tactics: _.map(techniqueCoverage.tactics, function(tactic) { 
            return tactic._id ? tactic : AttackService.index.tactics[tactic]
          })
        };
      })// end map
    }

    self.deferred = $q.defer();
    self.init = self.deferred.promise;

    $http.get('/api/analytics').success(function(analytics) {
        self.analytics = analytics;
        self.index = _.indexBy(analytics, '_id');
        self.deferred.resolve();

        // dereference all of the analytics, once ATT&CK is ready
        AttackService.init.then(function() {
            // initialize the 
            self.attackCoverage = {};
            _.each(AttackService.tactics, function(tactic) { 
              self.attackCoverage[tactic._id] = {};
            });

          _.each(analytics, function(analytic) {
            analytic.coverage = dereferenceCoverage(analytic.coverage);

            // selected is used for checkboxes in forms
            analytic.selected = analytic.enabled;

            _.each(analytic.coverage, function(coverage) {
              var techniqueId = coverage.technique._id;
              var level = coverage.level.toLowerCase();
              _.each(coverage.tactics, function(tactic) {
                var tacticId = tactic._id;
                var currentCoverage = self.attackCoverage[tacticId][techniqueId];
                if (currentCoverage === 'high' || level === 'high') {
                  self.attackCoverage[tacticId][techniqueId] = 'high';
                } else if (currentCoverage === 'moderate' || level === 'moderate') {
                  self.attackCoverage[tacticId][techniqueId] = 'moderate';
                } else if (currentCoverage === 'low' || level === 'low') {
                  self.attackCoverage[tacticId][techniqueId] = 'low';
                }
              });
            });


        });

      });
    });// end GET /api/analytics

    self.updateAnalytic = function(analytic) {
      // must already have the _id field satisfied
      // dereference the analytic from IDs to objects
      analytic.coverage = dereferenceCoverage(analytic.coverage);
      // check if it already has been loaded
      var existingAnalytic = self.index[analytic._id]
      if (existingAnalytic) {
        // replace it in the array and update the index
        var index = self.analytics.indexOf(existingAnalytic);
        self.analytics[index] = analytic;
        self.index[analytic._id] = analytic;
      } else {
        self.analytics.push(analytic);
        self.index[analytic._id] = analytic;
      }
    }

    self.removeAnalytic = function(analyticId) {
      // check if it has already been loaded
      var existingAnalytic = self.index[analyticId]
      if (existingAnalytic) {
        // replace it in the array and then update the index
        var index = self.analytics.indexOf(existingAnalytic);
        self.analytics.splice(index, 1);
        self.index[analyticId] = undefined;
      }
    }
  });

})();
