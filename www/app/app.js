(function() {
  var app = angular.module('cascade', [
    'ui.router',
    'ngCookies',
    'angular.filter'
  ]);


  // http://stackoverflow.com/questions/17772260/textarea-auto-height
  app.directive('elastic', [
    '$timeout',
    function($timeout) {
      return {
        restrict: 'A',
        link: function($scope, element) {
          $scope.initialHeight = $scope.initialHeight || element[0].style.height;
          var resize = function() {
            element[0].style.height = $scope.initialHeight;
            element[0].style.height = "" + element[0].scrollHeight + "px";
          };
          element.on("input change", resize);
          $timeout(resize, 0);
        }
      };
    }
    ]);

  app.directive('bstoggle', function() {
    return {
      restrict: 'A',
      link: function(scope, element, attributes) {
        var raw = attributes.toggleStrings.split('|');
        var id = attributes.id;
        
        element.bootstrapToggle('destroy').bootstrapToggle({on: raw[0], off: raw[1], onstyle:'primary', offstyle:'danger'});
      }
    }
  });


  app.config(function($stateProvider, $urlRouterProvider) {
    $urlRouterProvider.otherwise('/');

    $stateProvider.
      state('redirectIndex', {
        url: '/',
        views: {
          "content-block": {
            controller: function($state, $scope) {
                $state.go('index');
            }
          }
        }
      }).state('index', {
        url: '',
        views: {
          "head-block": {
            // templateUrl: "/app/index_head.html",
          },
          "content-block": {
            templateUrl: "/app/components/home/home.html",
            controller: function($state, $scope) {
              $scope.gotoLogin = function() {
                $state.go('login');
              }
            }
          }
        }
      }).state('debug', {
        url: '/debug',
        views: {
          "content-block": {
            template: ('<div>' +
              '<h1 style="text-align:center;">' +
              '<strong><code> DEBUG MODE </code><strong>' +
              '</h1></div>'
              ),
            controller: function($scope, $http) {
              // just to make life easier
              $http.get('/api/debug');
            }
          }
        }
      }).state('login', {
        url: '/login',
        params: {
            username: null
        },
        views: {
          "content-block": {
            templateUrl: "/app/components/account/login.html",
            controller: "LoginController"
          }
        }
      }).state('forgotPassword', {
        url: '/forgot-password',
        views: {
          "content-block": {
            templateUrl: "/app/components/account/forgot-password.html",
            controller: "ForgotPasswordController",
            controllerAs: 'ctrl'
          }
        }
      }).state('resetPassword', {
        url: '/reset-password?token&username',
        views: {
          "content-block": {
            templateUrl: "/app/components/account/reset-password.html",
            controller: "ResetPasswordController",
            controllerAs: 'ctrl'
          }
        }
      }).state('createAccount', {
        url: '/create-account',
        views: {
          'content-block': {
            templateUrl: '/app/components/account/create-account.html',
            controller: "CreateAccountController"
          }
        }
      }).state('createSession', {
        url: '/create-session',
        views: {
          'content-block': {
            templateUrl: '/app/components/session-form/create-session.html',
            controller: "CreateSessionController"
          }
        }
      }).state('attackClusters', { /* TODO: Place this somewhere */
        url: '/sessions/:sessionId/clusters/attack/:clusterindex',
        scope: {},
        views: {
          'head-block': {
            template: '<link type="text/css" href="/app/css/bargraph.css" rel="stylesheet"></link>'
          },
          'content-block': {
            template: '<div bar-graph tactics="tactics"></div>',
            controller: function($scope, $rootScope, $stateParams, $http) {
              var sessionId = $stateParams.sessionId;
              var clusterindex = $stateParams.clusterindex;
              $http.get('/api/sessions/' + sessionId + '/clusters/attack').success(function(data) {
                $scope.tactics = data[clusterindex].attack_summary.tactics;
              });
            }
          }
        }
      }).state('techniqueGraph', {
        url: '/sessions/:sessionId/graphs/attack',
        scope: {},
        views: { /*
          'head-block': {
            templateUrl: '/app/map_head.html'
          }, */
          'content-block': {
            templateUrl: '/app/common/directed-graph/session-graph.html',
            controller: 'TechniqueGraphController'
          }
        }
      }).state('alertGraph', {
        url: '/sessions/:sessionId/graphs/alerts',
        scope: {},
        views: { /*
          "head-block": {
            templateUrl: "/app/map_head.html",
          }, */
          'content-block': {
            templateUrl: '/app/common/directed-graph/session-graph.html',
            controller: 'AlertGraphController'
          }
        }
      }).state('hostsGraph', {
        url: '/sessions/:sessionId/graphs/hosts',
        scope: {},
        views: {
          "head-block": {
            // templateUrl: "/app/map_head.html",
          },
          'content-block': {
            templateUrl: '/app/common/directed-graph/session-graph.html',
            controller: 'HostGraphController'
          }
        }
      }).state('analyticTree', {
        url: '/sessions/:sessionId/graphs/analytic-tree',
        scope: {
          // 'selectedAnalytic': '=',
          // 'resultTree': '='
        },
        views: {
          "content-block": {
            templateUrl: "/app/components/tree-graphs/result-tree.html",
            controller: 'ResultTreeController'
          }
        }
      }).state('dataModel', {
        url: '/data-model',
        views: {
          'content-block': { 
            templateUrl: '/app/components/data-model/data-model.html',
            scope: {
              objects: '=',
              pivots: '=',
              glyphs: '='
            },
            controller: 'DataModelController'
          }
        }
      }).state('listAnalytics', {
        url: '/analytics',
        views: {
          'content-block': { 
            templateUrl: '/app/components/analytics-forms/list-analytics.html',
            scope: {
              analytics: '=',
              platforms: '=',
              format: '=',
              formats: '=',
              queries: '='
            },
            controller: 'ListAnalyticsController'
          }
        }
      }).state('analyticCoverage', {
        url: '/analytics/coverage',
        views: {
          'content-block': { 
            templateUrl: '/app/components/attack/analytic-coverage.html',
            scope: {
            },
            controller: 'AnalyticCoverageController'
          }
        }  
      }).state('modifyAnalytic', {
        url: '/analytics/modify/:analyticId',
        views: {
          'content-block': { 
            templateUrl: '/app/components/analytics-forms/modify-analytic.html',
            scope: {
              analytic: '='
            },
            controller: 'ModifyAnalyticController'
          }
        }
      }).state('createAnalytic', {
        url: '/analytics/create',
        views: {
          'content-block': { 
            templateUrl: '/app/components/analytics-forms/modify-analytic.html',
            scope: {
            },
            controller: 'ModifyAnalyticController'
          }   
        }
      }).state('eventMap', {
        url: '/sessions/:sessionId/graphs/events',
        views: {
          "head-block": {
            // templateUrl: "/app/map_head.html",
          }, 
          "content-block": {
            template: ('<div class="height-full pad-bottom">' +
                          '  <div event-graph events="events" results="results" style="height:calc(100% - 25px);"></div>' +
                          '  <div job-progress-bar filter="{\'session\': sessions.currentId}"></div>' +
                          '</div>'),
            scope: {},
            controller: 'EventMapController',
            controllerAs: 'mapCtrl'
          }
        }
      }).state('sessionHostTimeline', {
        url: '/sessions/:sessionId/host-timeline',
        views: {
          'content-block': {
            template: '<div class="height-full width-full"><h2>Host Timeline</h2><host-timeline class="height-full width-full" events="events"></host-timeline></div>',
            controller: 'EventMapController'
          }
        }
      }).state('sessionTimeline', {
        url: '/sessions/:sessionId/timeline',
        views: {
          'content-block': {
            template: '<div><h2>Event Timeline</h2><event-timeline events="events"></event-timeline></div>',
            controller: 'SessionTimelineController'
          }
        }
      }).state('dashboard', {
        url: '/sessions/:sessionId/dashboard',
        views: {
          'content-block': {
            templateUrl: '/app/components/dashboard/dashboard.html',
            controllerAs: 'ctrl',
            controller: "DashboardController"
          }
        }
      }).state('runAnalytics', {
        url: '/sessions/:sessionId/run-analytics',
        views: {
          "content-block": {
            templateUrl: '/app/components/analytics-forms/run-analytics.html',
            scope: { 
              // runMode: '=',
              getSelected: '='
            },
            controller: "RunAnalyticsController"
          }
        }
      }).state('attackMatrix', {
        url: '/attack/matrix',
        views: {
         'content-block': {
           templateUrl: '/app/components/attack/matrix.html'
         }
       }
      }).state('customQuery', {
        url: '/sessions/:sessionId/custom-query',
        views: {
          'content-block': {
            templateUrl: '/app/components/analytics-forms/run-custom.html',
            controller: "CustomQueryController"
          }
        }
      }).state('configureTacticSets', {
        url: '/attack/tactic-sets',
        views: {
          'content-block': {
            templateUrl: '/app/components/attack/tactic-sets.html',
            scope: {
              tacticSets: '=',
              newTacticSet: '='
            },
            controller: "TacticSetsController"
          }
        }
      }).state('configureAnalytics', {
        url: '/analytics/configure',
        views: {
          'content-block': {
            templateUrl: '/app/components/analytics-forms/configure-analytics.html',
            controller: "ConfigureAnalyticsController",
            controllerAs: "configCtrl"
          }
        }
      }).state('tuneAnalytics', {
        url: '/analytics/tuning',
        views: {
          'content-block': {
            templateUrl: '/app/components/analytics-forms/tune-analytics.html',
            controllerAs:'trainingCtrl',
            controller: "TuneAnalyticsController"
          }
        }
      }).state('tuneAnalytic', {
        url: '/analytics/tuning/:analyticId',
        views: {
          'content-block': {
            templateUrl: '/app/components/tuning/tuning.html',
            controller: "TuneAnalyticController"
          }
        }   
      }).state('account', {
        url: '/account',
        views: {
          "head-block": {
            template: ""
          },
          "content-block": {
            templateUrl: "/app/components/account/manage-account.html",
            controller: 'ManageAccountController',
            controllerAs:'dbCtrl'
          }
        }
      }).state('account-add-database', {
        url: '/account/add-database',
        views: {
          'content-block': {
            templateUrl: '/app/components/account/add-database-login.html',
            controller: "AddDatabaseController",
            controllerAs: 'addDbCtrl'
          }
        }
      }).state('manageExternalDatabases', {
        url: '/admin/databases',
        views: {
          'content-block': {
            templateUrl: '/app/components/databases/manage-databases.html',
            controller: "ManageDatabasesController",
          }
        }
      }).state('connectExternalDatabase', {
        url: '/admin/databases/connect',
        views: {
          'content-block': {
            templateUrl: '/app/components/databases/connect-database.html',
            controller: "ConnectDatabaseController",
            controllerAs: "dbCtrl"
          }
        }
      }).state('jobManager', {
        url: '/admin/jobs',
        views: {
          'content-block': {
            templateUrl: '/app/components/jobs/job-manager.html',
            controller: "JobManagerController",
            controllerAs: "jobCtrl"
          }
        }
      }).state('userGuide', {
        url: '/docs/user-guide',
        views: {
          'content-block': {
            templateUrl: '/docs/user-guide',
            controller: function($element) {
                $($element).find('a').on("click", function (clickEvent) {
                    var elem = $(clickEvent.toElement).attr('href');
                    if (elem && elem.startsWith('#') && !elem.startsWith("/#")) {
                        $('html, body').animate({scrollTop: $(elem).offset().top - 60});
                        return false;
                    }
                });
            }
          }
        }
      }).state('technicalGuide', {
        url: '/docs/technical-guide',
        views: {
          'content-block': {
            templateUrl: '/docs/technical-guide',
            controller: function($element) {
                $($element).find('a').on("click", function (clickEvent) {
                    var elem = $(clickEvent.toElement).attr('href');
                    if (elem && elem.startsWith('#') && !elem.startsWith("/#")) {
                        $('html, body').animate({scrollTop: $(elem).offset().top - 60});
                        return false;
                    }
                });
            }
          }
        }
      }).state('logout', {
        url: '/account/logout',
        views: {
          'content-view': {
            template: "<h1>TODO</h1>",
            controller: function($rootScope, $cookies, $state) {
            }
          }
        }
      });
  });/* end $stateProvider */

  app.run(function($rootScope, SessionService) {
    // automatically call
    $rootScope.$on('$stateChangeStart', function(event, toState, toParams, fromState, fromParams, options) {
      if (toParams.sessionId) {
        SessionService.init.then(function() {
            SessionService.activate(toParams.sessionId);
        });
      }
    });
  });


  // Check for login token
  // Load analytic info into memory
  app.run(function($rootScope, $http, $cookies, SessionService) {
    var token = $cookies.get("user-token");

    if (token) {
      $http.post("/api/login", {api_token: token}).success(function(data) {
        $rootScope.user = data;
        SessionService.refresh();
      });
    }
  });
})();
