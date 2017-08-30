(function() {
  var app = angular.module('cascade')
  app.requires.push('ui.bootstrap.datetimepicker');

  app.directive('analyticFormContent', function() {
    return {
      restrict: 'E',
      templateUrl: '/app/components/analytics-forms/analytics-form-base.html',
      scope: {
        platforms: '=',
        configuration: '=',  /* { analyticId: {mode: 'first-pass', status: true}, ... } */
        disableModes: '=?'
       /* editable: '=', */
       /* getSelected: '=' */
      },
      controllerAs: 'ctrl',
      controller: function($scope, $http, AttackService, AnalyticService) {
        var self = this;

        $scope.platforms = $scope.platforms || {};
        // use for filtering
        self.selectedTactic = null;
        self.selectedTechnique = null;

        $scope.modes = {'first-pass': 'First Pass',
                        'second-pass': 'Second-Pass',
                        'identify-only': 'Identify Only',
                        'identify-only-no-baseline': 'Identify Only (Skip Baseline)'
                        };

        AnalyticService.init.then(function () {
          $scope.analytics = AnalyticService.analytics;
          _.each($scope.analytics, function(analytic) {
            $scope.platforms[analytic.platform] = true;
          });
        });

        AttackService.init.then(function() {
            $scope.attack = AttackService;
        });
        // this should be deprecated
        /*
        $scope.getSelected = function() {
          return _.filter($scope.analytics, function(analytic) {
            return $scope.platforms[analytic.platform] && analytic.selected;
          });
        }
        */

        // filter these dynamically from the search box and from the tactic/techniques
        self.filter = function(value, index, array){

          var techniques = [],
          tactics = [];

          if(value.coverage){

            value.coverage.forEach(function(item){
              techniques.push(item.technique.name);
              item.tactics.forEach(function(tactic){
                tactics.push(tactic.name);
              });
            });
          }

          var res = true;

          if(self.selectedTactic){
            res = tactics.indexOf(self.selectedTactic.name) !== -1;
          }

          if(self.selectedTechnique){
            res = res && techniques.indexOf(self.selectedTechnique.name) !== -1;
          }

          if(self.searchQuery){
            var searchHit = value.description &&
            value.description.indexOf(self.searchQuery) !== -1 ||
            value.name &&
            value.name.indexOf(self.searchQuery) !== -1;

            res = res && searchHit;
          }

          return res;
        };

        $scope.showPlatform = function(platform) {
          $scope.platforms[platform] = true;
          _.each($scope.analytics, function(analytic) {
            analytic = analytic.platform ? analytic.selected : analytic.status;
          });

          return false;
        };
      }
    }
  });

})();