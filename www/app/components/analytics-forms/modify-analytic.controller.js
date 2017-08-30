(function() {
  var app = angular.module('cascade');

  app.controller('ModifyAnalyticController', function($http, $stateParams, $scope, $rootScope, $state, AnalyticService, AttackService) {
      $scope.platforms = ['CASCADE', 'Splunk', 'ElasticSearch', 'MongoDB'];
      $scope.modes = {/*'realtime': 'Real-Time (Beta)', */'first-pass': 'First Pass', 'second-pass': 'Second-Pass'};
      $scope.levels = ['Low', 'Moderate', 'High'];
      $scope.queryText = '';
      // expose this to view
      $scope.attack = AttackService;
      $http.get('/api/data_model/objects').success(function(dataModel) {
        $scope.dataModel = dataModel;
        $scope.dataModelIndex = _.indexBy(dataModel, 'name');
      });

      $scope.mappedEventList = [];

      AnalyticService.init.then(function() {
        AttackService.init.then(function() {
          if ($stateParams.analyticId) {
            var analyticId = $stateParams.analyticId;
            var analytic = AnalyticService.index[analyticId];

            // deep copy it
            $scope.analytic = $.extend(true, {}, analytic);

            if ($scope.analytic.platform === 'CASCADE') {
                $http.get('/api/analytics/' + analyticId + '/lift').success(function(query) {
                    $scope.queryText = query.text;
                });
            } else {
                $scope.mappedEventList = _.map($scope.analytic.mapped_events, function(mappedEvent) {
                    return {
                        object: mappedEvent.object,
                        action: mappedEvent.action,
                        fieldMap: _.map(Object.keys(mappedEvent.fields || {}), function(field) {
                                return {field: field, externalField: mappedEvent.fields[field]};
                        })
                    };
                });
            }
          } else {
            $scope.analytic = {coverage: [], mapped_events: [], enabled: true, mode: 'first-pass', query: null, platform: 'CASCADE'};
            $scope.mappedEventList = [{fieldMap: [{}]}];
          }
        });
      });

      function resetCurrentCoverage() {
        $scope.currentCoverage = {technique: null, tactics: [], level: 'Moderate'};
      }

      resetCurrentCoverage();

      $scope.$watch('selectedTechnique', function() {
        $scope.selectedTactics = {};
      });

      $scope.addCoverage = function() {
        if ($scope.currentCoverage.technique) {
          var tactics = [];
          _.each($scope.selectedTactics, function(status, tacticId) {
            if (status) {
              tactics.push(AttackService.index.tactics[tacticId]);
            }
          })
          $scope.currentCoverage.tactics = tactics;
          $scope.analytic.coverage.push($scope.currentCoverage);
          resetCurrentCoverage();
        }
      }

      $scope.$watch('queryText', function()  {
        if ($scope.queryText) {
          $http.post('/api/query/parse', {query: $scope.queryText}).then(function(queryData) {
            var query = queryData.data;
            $scope.analytic.mapped_events = [{object: query.object, action: query.action}];
            $scope.query = query.query;
            $scope.error = false;
          }, function(failure) {
            $scope.error = true;
            $scope.errorText = failure.data.error;
          });
        }
      });

      $scope.icon = 'disk';
      function iconTimer(newIcon) {
        $scope.icon = newIcon;
        setTimeout(function() {
            $scope.$apply(function () {
                $scope.icon = 'disk';
            });
        }, 2500);
      }
      // update the existing analytic
      $scope.submit = function() {
          // copy it first, because "coverage" in the API is different
          // than analytic.coverage for this view
          var updatedAnalytic = $.extend({}, $scope.analytic);
          updatedAnalytic.selected = undefined;
          updatedAnalytic.coverage = _.map(updatedAnalytic.coverage, function(techniqueCoverage) {
            return {
              technique: techniqueCoverage.technique._id,
              tactics: _.map(techniqueCoverage.tactics, function(tactic) { return tactic._id}),
              level: techniqueCoverage.level
            };
          });

          if (updatedAnalytic.platform !== 'CASCADE') {
            updatedAnalytic.mapped_events = _.map($scope.mappedEventList, function(mappedEvent) {
                var mappingDict = {};
                _.each(mappedEvent.fieldMap, function(mapKey) {
                    if (mapKey.field && mapKey.externalField) {
                        mappingDict[mapKey.field] = mapKey.externalField;
                    }
                });
                return {object: mappedEvent.object, action: mappedEvent.action, field_map: mappingDict};
            });
          }

        function createAnalytic() {
          $http.post('/api/analytics', updatedAnalytic).success(function(analyticId) {
            $scope.analytic._id = analyticId
            iconTimer('saved');
            $http.get('/api/analytics/' + analyticId).success(function(analytic) {
                AnalyticService.updateAnalytic(analytic);
                $state.go('modifyAnalytic', {analyticId: analyticId});
            })
          });
        }


        function updateAnalytic() {
          var analyticId = updatedAnalytic.id = updatedAnalytic._id;
          if (analyticId == undefined) {
            return createAnalytic();
          }
          updatedAnalytic._id = undefined;
          $http.put('/api/analytics/' + analyticId, updatedAnalytic).success(function(analytic) {
            iconTimer('saved');
            AnalyticService.updateAnalytic(analytic);
             // alert('Analytic updated successfully');
          }).catch(function(error) {
             alert('Analytic not updated successfully');
             //iconTimer('remove');
          });
        }

        if (updatedAnalytic.platform !== 'CASCADE') {
          updatedAnalytic.query = undefined;
          updateAnalytic();
        } else {
          var query;
          // CASCADE analytics require verification of query langauge before submitting
          $http.post('/api/query/parse', {query: $scope.queryText}).success(function(query) {
            updatedAnalytic.mapped_events = [{object: query.object, action: query.action}];
            updatedAnalytic.query = query.query;

            updateAnalytic();
          });
        }
      }

      $scope.remove = function() {
        if (confirm("Are you sure you want to remove the analytic " + $scope.analytic.name)) {
          $http.delete('/api/analytics/' + $scope.analytic._id).then(function(success) {
            var status = success.data;
            alert('Successfully removed analytic');
            AnalyticService.removeAnalytic($scope.analytic._id);
            $state.go('createAnalytic');
          }, function(failure) {
            alert('ERROR removing analytic');
          });
        }
      }
  });
})();