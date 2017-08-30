(function() {
  var app = angular.module('cascade');
  app.directive('fileUpload', function() {
    return {
      restrict: 'A',
      scope: {
        file: "="
      },
      link: function(scope, elem, attrs) {
        scope.elem = elem;

        elem.bind('change', function() {
          scope.$apply(function(){
            console.log(elem);
            if (elem[0].files) {
              scope.file = elem[0].files[0];
            } else {
              scope.file = {name: "no file"};
            }
          });
        });
      }
    }
  });
})();