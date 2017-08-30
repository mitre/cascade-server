(function() {
  var app = angular.module('cascade');

  app.controller('JobManagerController', function($http, $cookies, $scope, $state, AnalyticService, SessionService) {
        var self = this;
        self.clear = function(key) {
            if (key) {
                delete $scope.jobFilter[key];
            } else {
                $scope.jobFilter = {};
            }
        };
        $scope.jobFilter = {};
        $scope.jobPages = [];
        $scope.pageNum = 0;
        $scope.pageSize = 50;
        $scope.jobOffset = 0;

        SessionService.init.then(function() {
            $scope.sessionIndex = SessionService.index;
        });

        AnalyticService.init.then(function() {
            $scope.analyticIndex  = AnalyticService.index;
        })

        self.loadJobs = function() {
            $http.get('/api/jobs').success(function(jobs) {
                self.loaded = true;
                $scope.jobs = jobs;
                $scope.$watch('jobFilter', function() {
                    $scope.filteredJobs = _.where($scope.jobs, $scope.jobFilter);
                    $scope.pages = [];
                    var numPages = Math.ceil($scope.filteredJobs.length / $scope.pageSize);
                    for (var i=0; i < numPages; i++) {
                        $scope.pages.push(i * $scope.pageSize);
                    }
                    $scope.jobOffset = 0;
                }, true);

                $scope.pageNum = 0;
            });
    	}

    	self.loadJobs();

    	self.updateStatus = function(status) {
    	    var params = $.extend({multi: true}, $scope.jobFilter);
            $http.post('/api/jobs', {status: status}, {params: params}).success(function() {
                self.loadJobs();
            });
    	}

    	self.removeJobs = function() {
    	    var params = $.extend({multi: true}, $scope.jobFilter);
    	    if (confirm("Are you sure you want to remove " + $scope.filteredJobs.length + " jobs?")) {
    	        $http.delete('/api/jobs', {params:params}).success(function() {
    	            $scope.jobFilter = {};
    	            self.loadJobs();
    	        });
    	    }
    	}
    });
})();