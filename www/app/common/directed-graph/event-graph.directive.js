(function() {
    angular.module('cascade').directive("eventGraph", function() {
      return {
        restrict: 'A',
        template: '<div d3-graph links="links" nodes="nodes" class="height-full" active-node="activeNode"></div>',
        scope: {
          events: '=',
          results: '=',
          activeNode: '=?'
        },
        controller: function($scope, $http, AttackService, AnalyticService, SessionService) {
          var self = this;

          $scope.nodes = [];
          $scope.links = [];
          self.index = {nodes: {}, connections: {}, links: {}};

          SessionService.init.then(function() {
              $scope.$watch('activeNode.investigate', function() {
                if ($scope.activeNode && $scope.activeNode.investigate) {
                    $scope.activeNode.investigate = undefined;
                    var uri = '/api/sessions/' + SessionService.currentId + '/automate/event/' + $scope.activeNode.id;
                    $http.post(uri).success(function(result) {

                    });
                }
              });
          });

          function createTooltip(node) {
            var tooltip  =  "id    \t" + node.id + "\n";

            if (node.time || node.item.time) {
                tooltip  += "time  \t" + (node.time || node.item.time) + "\n\n";
            }

                tooltip +=  "type  \t" + node.group + "\n";

            if (node.item.action) {
                tooltip +=  "action \t" + node.item.action + "\n";
            }

                tooltip +=  "\n";
                tooltip += node.title + "\n";
                tooltip += node.subtitle + "\n";
           /*
            var event = node.item;
            var tooltip = [];
            for (var key in event) {
              if (key ==='links'|| key==='reverse_links' || key === 'metadata') {
                continue;
              }
              var val = event[key];
              var current_tooltip = key + '\t' + val;
              if (typeof val === 'object') {
                var fields = [];
                for (var k2 in val) {
                  fields.push('\t' + k2 + '\t' + val[k2]);
                }
                current_tooltip = key + '\n' + fields.sort().join('\n');
              }
              tooltip.push(current_tooltip);
            }
            return tooltip.sort().join("\n");
            */
            return tooltip;
          }

          function addNode(item, family, title, subtitle) {
            var itemId = item._id || item.id;
            // TODO: maybe skip the indexing for now -- it might be causing things to break
            var node = {id: itemId, item: item}
            node.title = title || "";
            node.subtitle = subtitle || "";
            node.family = family || item.object_type;
            node.group = item.object_type || family || "unknown";
            node.tooltip = createTooltip(node);

            self.index.nodes[itemId] = node;
            $scope.nodes.push(node);
            return node;
          }

          $scope.$watchGroup(['events', 'events.length', 'results', 'results.length'], function() {
            // remove nodes that went missing!
            var eventIndex = _.indexBy($scope.events, '_id');
            var resultIndex = _.indexBy($scope.results, '_id');
            var existingLinks = _.filter($scope.links, function(link) {
                return link.source && link.target && eventIndex[link.source.id] && eventIndex[link.target.id];
            });
            var existingNodes = _.filter($scope.nodes, function(node) {
                return eventIndex[node.id] || resultIndex[node.id];
            });

            // rebuild the node index, so removed nodes aren't present
            self.index.nodes = _.indexBy($scope.nodes, 'id');

            // d3 freaks out if you replace the links and nodes arrays, so instead these need to be modified in place
            $scope.nodes.length = 0;
            $scope.links.length = 0;

            Array.prototype.push.apply($scope.nodes, existingNodes);
            Array.prototype.push.apply($scope.links, existingLinks);

            // rebuild the connections index
            var connectionIndex = {};
            _.each(self.index.connections, function(connectionNode, indexId) {
                if (self.index.nodes[connectionNode.id]) {
                    connectionIndex[indexId] = connectionNode;
                }
            });

            self.index.connections = connectionIndex;

            // this will be called on any changes, so everything needs to be re-enumerated
            // because there's no way to keep track of what has and has not yet been processed

            _.each($scope.events, function(event) {
                var eventId = event._id;
                // skip events that have already been indexed
                if (self.index.nodes[eventId]) {
                    return;
                }

                if (event.object_type === 'process') {
                  if (event.action !== 'terminate') {
                    var shortName = (event.state.exe || event.state.image_path || "").split("\\").pop();
                    if (shortName.length > 16) {
                      var nameParts = shortName.split(".");
                      var ext = "." + nameParts.pop();
                      shortName = nameParts.join(".");
                      shortName = shortName.substring(0, 16 - ext.length - 4) + "[...]";
                    }

                    addNode(event, "event", shortName, String(event.state.user || "").split("\\").pop());
                  }

                } else if (event.object_type === 'file') {
                    var ext = (event.state.file_name || event.state.file_path || "").split('.').pop().toLowerCase();
                    var shortName = event.state.file_name;

                    if (shortName.length > 16) {
                      var nameParts = shortName.split(".");
                      var ext = "." + nameParts.pop();
                      shortName = nameParts.join(".");
                      shortName = shortName.substring(0, 16 - ext.length - 4) + "[...]";
                    }

                    addNode(event, "event", shortName, (event.state.user || "").split("\\").pop());

                } else if (event.object_type === 'flow') {
                    // collapse all connection for the process
                    var newUuid = [event.state.dest_ip, event.state.dest_port,
                                   event.state.src_ip,
                                   event.state.hostname,
                                   event.state.pid].join('-');

                    var connectionNode = self.index.connections[newUuid];

                    if (!connectionNode) {
                      self.index.connections[newUuid] = event;
                      event._connectionCount = 1;
                      connectionNode = addNode(event, "event", event.state.dest_ip, event.state.dest_port);
                    } else {
                      // if already exists, then alias the node, and update the subtitle
                      self.index.nodes[event._id] = self.index.nodes[connectionNode.id];
                      // TODO: maybe update the time field to min(matchingConnection.item.time, event.time)
                      connectionNode.subtitle = event.state.dest_port + ' (' + (++connectionNode._connectionCount) + ')'
                    }
                } else if (event.object_type === 'user_session') {
                    addNode(event, "event", event.state.user, event.state.action);

                } else if (event.object_type === 'thread') {
                    addNode(event, "event", event.state.target_exe, event.state.target_pid);

                } else if (event.object_type == 'registry') {
                    // TODO: Handle events other than SetValue, such as CreateKey, etc.
                    addNode(event, "event", event.state.value, event.state.data);

                } else {
                    // if unknown, then add object generically
                    addNode(event, "event", event.object_type, event.action);
                }
            });

            // assume that result.analytic is already dereferenced to the analytic object
            _.each($scope.results, function(result) {
                var resultId = result._id;
                var resultNode = self.index.nodes[resultId];
                // skip events that have already been indexed
                if (!resultNode) {
                    resultNode = addNode(result, "analytic_result", "Analytic Result", result.analytic.name)
                }

                _.each(result.events, function(eventId) {
                    var eventNode = self.index.nodes[eventId];
                    // todo: double check that the link hasn't already been added to avoid doing double links
                    if (eventNode && eventNode.item) {
                      $scope.links.push({source: eventNode, target: resultNode, value: 1, weight: 1});
                    }
                });
            });

            // Walk through events and update links
            _.each($scope.events, function(event) {
              var sourceNode = self.index.nodes[event._id];
              if (!sourceNode || !sourceNode.item) {
                return;
              }

              _.each(event.links, function(linkId) {
                var targetNode = self.index.nodes[linkId];
                // TODO: double check that the link hasn't already been added to avoid doing double links
                if (targetNode && targetNode.item) {
                  $scope.links.push({source: sourceNode, target: targetNode, value: 1, weight: 1});
                }
              });
            }); // end of link walk through nodes

          });
        } // function() { }
      } // return {controller: function() ... }
    }); // angular.module( ... )
})();