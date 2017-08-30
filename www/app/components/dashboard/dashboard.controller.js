(function() {
  var app = angular.module('cascade');

  app.controller('DashboardController',function($scope, $http, $stateParams, AttackService, AnalyticService, SessionService) {
      var self = this;

      $scope.sessionId = self.sessionId  = $stateParams.sessionId;
      self.techniqueMap = {};
      self.tacticMap = {};

      $scope.showAll = false;

      SessionService.init.then(function() {
        self.sessions = SessionService;
        $scope.analyticState = _.indexBy(self.sessions.current.state.analytics, 'analytic');
      });

      $scope.toggleClusters = function(){
        $scope.showAll = !$scope.showAll;
      };

      self.changeProp = function(key) {
        $scope.sortDir = ($scope.sortProp === key) ? (!$scope.sortDir) : false;
        $scope.sortProp = key;
      }

      function zeroPad(number) {
        var digits = 12;
        var str = number.toFixed(4).toString();
        var padStr = "0".repeat(digits - str.length) + str;
        return padStr;
      }


      self.sort = function(key) {
          return function(cluster) {
            if (key === 'events') {
                return zeroPad((cluster.events).length);
            } else if (key === 'alerts') {
                return zeroPad((cluster.results).length);
            } else if (key === 'tactics') {
                cluster.tactics = cluster.tactics;
                return zeroPad(cluster.attack_summary.tactics.length) + " " + zeroPad(cluster.attack_summary.counts.tactics) + " " + cluster.tactics.map(x => x.tactic.name).join(",");
            } else if (key === 'techniques') {
                cluster.techniques = cluster.techniques || [];
                return  zeroPad(cluster.attack_summary.techniques.length) + " " + zeroPad(cluster.attack_summary.counts.techniques) + " " + cluster.techniques.map(x => x.technique.name).join(",");
            } else if (key === 'ratio') {
                return zeroPad((cluster.results).length / (cluster.events).length);
            } else if (key === 'hosts') {
                cluster.hosts = cluster.hosts;
                if ($scope.hostIndex) {
                    return zeroPad(cluster.hosts.length) + " " + cluster.hosts.map(hostId => ($scope.hostIndex[hostId] || {}).hostname || hostId).sort().join(",");
                }
            } else if (key === 'tacticSet') {
                return cluster.tactic_sets.length;
            }
            return cluster;
          }
      }

      $scope.thresholds = {tactics: 1, techniques: 1, distinct: true};

      self.filter = function(value, index, array) {
        var distinct = $scope.thresholds.distinct || false;
        var status = true;
        if (status && $scope.thresholds.tactics) {
            if (distinct) {
                status = status && (value.attack_summary.tactics.length >= $scope.thresholds.tactics);
            } else {
                status = status && (value.attack_summary.counts.tactics >= $scope.thresholds.tactics);
            }
        }

        if (status && $scope.thresholds.techniques) {
            if (distinct) {
                status = status && (value.attack_summary.techniques.length >= $scope.thresholds.techniques);
            } else {
                status = status && (value.attack_summary.counts.techniques >= $scope.thresholds.techniques);
            }
        }
        return status;
      }

      $scope.selected = {};
      AttackService.init.then(function() {
          $scope.attack = AttackService;
          $scope.$watch('selected', function() {
            var heatMap = {};
            _.each(AttackService.tactics, function(tactic) {
                heatMap[tactic._id] = {};
            });

            $scope.summary = {events: [], results: [], hosts: [], tactics: [], techniques: [], count: 0, heatMap: heatMap};
            _.each($scope.selected, function(status, index) {
                if (status) {
                    $scope.summary.count++;
                    var cluster = $scope.clusters[index];
                    Array.prototype.push.apply($scope.summary.events, cluster.events);
                    Array.prototype.push.apply($scope.summary.results, cluster.results);
                    /*
                    // todo: make these unique based off of values/keys
                    if ($scope.hostIndex) {
                        cluster.hosts = _.sortBy(cluster.hosts, function(hostId) {
                            var host = $scope.hostIndex[hostId];
                            return host ? host.hostname : hostId;
                        });
                    }
                    */

                    Array.prototype.push.apply($scope.summary.hosts, cluster.hosts);
                    Array.prototype.push.apply($scope.summary.tactics, cluster.tactics);
                    Array.prototype.push.apply($scope.summary.techniques, cluster.techniques);

                    _.each(cluster.heatMap, function(tacticMap, tacticId) {
                        _.each(tacticMap, function(techniqueCount, techniqueId) {
                            heatMap[tacticId][techniqueId] = (heatMap[tacticId][techniqueId] || 0) + techniqueCount;
                        });
                    })
                }
            });

            var uniqueHostIds = Array.from(new Set($scope.summary.hosts));
            $scope.summary.hosts = _.map(uniqueHostIds, function(hostId) {
                return $scope.hostIndex[hostId];
            });
          }, true);
      });

      $http.get('/api/sessions/' + self.sessionId + '/hosts')
        .success(function(data){
            $scope.hosts = data;
            $scope.hostIndex = _.indexBy(data, '_id');
      })

      $http.get('/api/sessions/' + self.sessionId + '/events')
      .success(function(data){
        $scope.events = data;
      });


      $http.get('/api/sessions/' + self.sessionId + '/results')
      .success(function(results) {
        $scope.results = results;
        AnalyticService.init.then(function() {
            var analyticCounts ={};
            _.each($scope.results, function(result) {
                var analyticId = result.analytic;
                var analytic = AnalyticService.index[analyticId];
                result.analytic = analytic;
                analyticCounts[analyticId] = analyticCounts[analyticId] || {count: 0, results: []};
                analyticCounts[analyticId].count++;
                analyticCounts[analyticId].results.push(result);
                analyticCounts[analyticId].analytic = analytic;
            });
            $scope.analyticCounts = _.map(Object.keys(analyticCounts), function(analyticId) {
                return analyticCounts[analyticId];
            });
        });

      });

      $http.get('/api/sessions/' + self.sessionId + '/clusters/attack').success(function(data) {
        AttackService.init.then(function() {
            $scope.clusters = data;

            if(_.isEmpty(self.techniqueMap)){
              self.techniqueMap = _.indexBy(AttackService.techniques, '_id');
            }

            if(_.isEmpty(self.tacticMap)){
              self.tacticMap = _.indexBy(AttackService.tactics, '_id');
            }

            // sort the hosts based off of the hostname field
            $scope.$watch('hostIndex', function() {
                if ($scope.hostIndex) {
                    _.each($scope.clusters, function(cluster) {
                        cluster.hosts = _.sortBy(cluster.hosts, function(hostId) {
                            var host = $scope.hostIndex[hostId];
                            return host ? host.hostname : hostId;
                        });
                    });
                }
            });


            _.each($scope.clusters, function(cluster, index) {
              var events  = cluster.events,
                  results = cluster.results,
                  summary = cluster.attack_summary;

              cluster.index = index;

              var eventIndex = _.indexBy(events, '_id');
              AnalyticService.init.then(function() {
                _.each(results, function(result) {
                    result.analytic = AnalyticService.index[result.analytic];

                    if (!result.analytic) {
                        return;
                    }

                    _.each(result.events, function(eventId) {
                        var event = eventIndex[eventId];
                        if (!event) {
                            return;
                        }
                        event.attack = event.attack || {techniques: [], tactics: []};
                        _.each(result.analytic.coverage, function(coverage) {
                            var techniqueName = coverage.technique.name;
                            if (event.attack.techniques.indexOf(techniqueName) == -1) {
                                event.attack.techniques.push(techniqueName);
                            }
                            _.each(coverage.tactics, function(tactic) {
                                var tacticName = tactic.name;
                                if (event.attack.tactics.indexOf(tacticName) == -1) {
                                    event.attack.tactics.push(tacticName);
                                }
                            });
                        });
                    });
                });
              });


              cluster.heatMap = {};
              _.each(AttackService.tactics, function(tactic) { cluster.heatMap[tactic._id] = {}; })
              _.each(summary.tuples, function(tuple) {
                var techniqueId = tuple.technique;
                _.each(tuple.tactics, function(tacticId) {
                  cluster.heatMap[tacticId][techniqueId] = (cluster.heatMap[tacticId][techniqueId] || 0) + tuple.count;
                });
              });

              cluster.tactics = summary.tactics.map(function(tactic) {
                // tactic = {tactic: <ID>, count: count}
                return {tactic: AttackService.index.tactics[tactic.tactic], count: tactic.count};
              });


              cluster.techniques = summary.techniques.map(function(technique) {
                // tactic = {tactic: <ID>, count: count}
                return {technique: AttackService.index.techniques[technique.technique], count: technique.count};
              });


              cluster.hosts = Array.from(new Set(events.map(function(e){ return e.host})));
              cluster.tactic_sets = summary.tactic_sets;
              cluster.detection_rate = (cluster.results.length / cluster.events.length);
            });
        });
      });

      /*
      self.highlightMatrix = function(index){
        $scope.cluster = $scope.clusters[index];
      };
      */
    });
})();

