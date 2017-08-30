(function() {
  var app = angular.module('cascade');

  app.controller('CustomQueryController', function($http, $stateParams, $scope, $state, AttackService) {
      var self = this;
      self.sessionId = $stateParams.sessionId;
      $scope.modes = {'first-pass': 'First Pass', 'second-pass': 'Second-Pass'};
      $scope.platforms = ['CASCADE', 'Splunk', 'ElasticSearch', 'MongoDB'];
      $scope.levels = ['Low', 'Moderate', 'High'];
      $scope.platform = 'CASCADE'
      $scope.error = false;
      $scope.queryText = '';
      $scope.coverage = [];
      $scope.mapped_events = [];

      AttackService.init.then(function() {
        $scope.attack = AttackService;
      });

      function resetCurrentCoverage() {
        $scope.currentCoverage = {technique: null, tactics: [], coverage: 'Moderate'};
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
              tactics.push($scope.attack.index.tactics[tacticId]);
            }
          })
          $scope.currentCoverage.tactics = tactics;
          $scope.coverage.push($scope.currentCoverage);
          resetCurrentCoverage();
        }
      }

      $scope.$watch('queryText', function()  {
        if ($scope.queryText) {
          $http.post('/api/query/parse', {query: $scope.queryText}).then(function(queryData) {
            var query = queryData.data;
            $scope.mapped_events = [{object: query.object, action: query.action}];
            $scope.query = query.query;
            $scope.error = false;
          }, function(failure) {
            $scope.error = true;
            $scope.errorText = failure.data.error;
          });
        }
      });

      $scope.submit = function()  {
        $http.post('/api/query/parse', {query: $scope.queryText}).success(function(query) {
          $scope.error = false;
          $scope.query = query.query;
          $scope.mapped_events = [{object: query.object, action: query.action}];
          var coverage = _.map($scope.coverage, function(techniqueCoverage) {
            return {
              technique: techniqueCoverage.technique._id,
              tactics: _.map(techniqueCoverage.tactics, function(tactic) { return tactic._id}),
              coverage: techniqueCoverage.coverage
            };
          });

          $http.post('/api/sessions/' + self.sessionId + '/automate/custom', {query: $scope.query}).success(function(result) {
            console.log('success');
            $state.go('dashboard', {sessionId: self.sessionId});
          }).catch(function(failure) {
            $scope.error = true;
            $scope.errorText = 'Error when running query';
          });

        }).catch(function(failure) {
          $scope.error = true;
        });
      }
    });
})();

