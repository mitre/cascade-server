(function() {

  var app = angular.module('cascade');
  app.requires.push('ngSanitize');

  app.directive('datatable', function() {
    return {
      // restrict: 'A',
      templateUrl: '/app/common/datatable/datatable.html',
      scope: {
        rows: "=",
        columns: "=",
        headers: "=?",
        htmlBind: '=?'
      },
      controller: function($scope) {
          $scope.isArray = function (obj) {
            return Array.isArray(obj);
          }

          var self = this;
          self.sortProp = $scope.columns.length ? $scope.columns[0] : null;
          self.sortBool = false;

          self.orderTable = function(prop) {
            if (prop == self.sortProp) {
                self.sortBool = !self.sortBool;
            } else {
                self.sortProp = prop;
                self.sortBool = false;
            }
          }

      },
      controllerAs: 'datatableCtrl'
    }
  });
})();