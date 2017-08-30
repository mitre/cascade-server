var globalForce;
(function() {
    angular.module('cascade').directive("d3Graph", function() {
       // TODO: switch some things to self if possiblef
      return {
        restrict: 'A',
        templateUrl: '/app/common/directed-graph/svg-container.html',
        scope: {
          nodes: '=',
          links: '=',
          activeNode: '=?'
        },
        controller: function($scope, $window, SessionService) {
            var self = this;
            $scope.groups = [];

            // use this to enable the re-investigate window
            SessionService.init.then(function() {
                $scope.sessionId = SessionService.currentId;
            });

            function updateGraph() {
              $scope.force.stop();
              $scope.force.nodes($scope.nodes).links($scope.links);

              function getRadius(n) {
                return n.r = (12 + (n.title || "...").length * 3.5) || 5;
              }


              $scope.linkElems = $scope.container
                              .select('.links')
                                    .selectAll('.link')
                                    .data($scope.force.links());

              $scope.nodeElems = $scope.container
                                      .select('.nodes')
                                          .selectAll('.node')
                                          .data($scope.force.nodes(), function(n) { return n.id});

              /*
              $scope.nodeElems.selectAll('text').text(function(d) {
                //console.log(d);
                return 'pending update...';
              });
              */

              $scope.linkElems.enter()
                       .append('line')
                       .attr('class', 'link')
                        .style("marker-end", "url(#arrowhead)");
              $scope.linkElems.exit().remove();

              function getClass(d) {
                var classes = ['node'];
                if (!(d.metadata && d.metadata.highlight)) {
                  classes.push('hightlight');
                }
                if (d.group) {
                  classes.push(d.group);
                  if ($scope.groups.indexOf(d.group) == -1) {
                      $scope.groups.push(d.group);
                  }
                }
                return classes.join(' ');
              }


              $scope.nodeElems.selectAll('title')
                              .text(function(d) {  return d.tooltip; });

              // update existing nodes
              $scope.nodeElems.attr('class', getClass);

              $scope.nodeElems.selectAll('circle')
                      .attr('r', getRadius);
              $scope.nodeElems.selectAll('.title')
                     .attr('y', function(n) { return n.subtitle ? 0 : ".5em" })
                     .text(function(n) { return n.title; });
              $scope.nodeElems.selectAll('.subtitle')
                      .text(function(n) { return n.subtitle; });

              var newNodes = $scope.nodeElems.enter()
                      .append('svg:g');
              $scope.nodeElems.exit().remove();


              $scope.nodeElems.selectAll('title')
                              .text(function(d) {
                                return d.tooltip;
                              });

              // update existing nodes
              $scope.nodeElems.attr('class', getClass);

              $scope.nodeElems.selectAll('circle')
                      .attr('r', getRadius);
              $scope.nodeElems.selectAll('.title')
                     .attr('y', function(n) { return n.subtitle ? 0 : ".5em" })
                     .text(function(n) { return n.title; });
              $scope.nodeElems.selectAll('.subtitle')
                      .text(function(n) { return n.subtitle; });

              // var updatedNodes = $scope.nodeElems.update().selectAll('svg:g');


              newNodes.call($scope.force.drag().on('dragstart', function(n) {
                d3.event.sourceEvent.stopPropagation();
                d3.select(this).classed("fixed", n.fixed = true);
                $scope.activeNode = n;
                // this event didn't come from angular, so need to force update
                $scope.$apply();
              }));


              //TODO: Pretty print string
              newNodes.append('svg:title').text(function(d) {
                return d.tooltip;
              });

              newNodes.insert('circle')
                      .attr('r', getRadius);
              newNodes.insert('text')
                     .attr('class', 'title')
                     .attr('text-anchor', 'middle');

              newNodes.insert('text')
                      .attr('class', 'subtitle')
                      .attr('text-anchor', 'middle')
                      .attr('y', "1em")
                      .text(function(n) { return n.subtitle; });

              $scope.nodeElems.selectAll('title')
                              .text(function(d) {  return d.tooltip; });

              // update existing nodes
              $scope.nodeElems.attr('class', getClass);

              $scope.nodeElems.selectAll('circle')
                      .attr('r', getRadius);
              $scope.nodeElems.selectAll('.title')
                     .attr('y', function(n) { return n.subtitle ? 0 : ".5em" })
                     .text(function(n) { return n.title; });
              $scope.nodeElems.selectAll('.subtitle')
                      .text(function(n) { return n.subtitle; });

              /*
              var circle = newNodes.insert('circle')
                      .attr('r', getRadius);
              var label = newNodes.insert('text')
                     .attr('class', 'title')
                     .attr('text-anchor', 'middle')
                     .attr('y', function(n) { return n.subtitle ? 0 : "1em" })
                     .text(function(n) { return n.title; });

              var subtitle = newNodes.insert('text')
                      .attr('class', 'subtitle')
                      .attr('text-anchor', 'middle')
                      .attr('y', "1em")
                      .text(function(n) { return n.subtitle; });
              */

              // $scope.label = $scope.nodeElems.selectAll('text');
              // $scope.circle = $scope.nodeElems.selectAll('circle');

              // remove DOM elements for data-bound items that are no longer present


              // update existing nodes
              /*
              $scope.nodeElems.attr('class', getClass);

              $scope.nodeElems.selectAll('circle').transition()
                      .attr('r', function(n) {
                        console.log(n);
                        n.fixed = false;
                        return getRadius(n);
                      });
              $scope.nodeElems.selectAll('.title').transition()
                     .attr('y', function(n) { return n.subtitle ? 0 : ".5em" })
                     .text(function(n) {
                        return n.title;
                     });
              $scope.nodeElems.selectAll('.subtitle').transition()
                      .text(function(n) { return n.subtitle; });
              */

              $scope.force.start();
            }

            $scope.$watchGroup(['nodes', 'nodes.length', 'links', 'links.length'], function() {
                updateGraph();
          });
        },
        link: function(scope, elem, attrs) {
          var height = elem[0].offsetHeight;
          var width = elem[0].offsetWidth;
          var region = d3.select(elem[0]).select('.svg-container'); //attr("class", "rounded height-full").style("border-style", "solid").style("border-width", 1);
          var force = d3.layout.force()
                  .charge(function(n) {
                    // assuming constant charge density, total charge should be proportional to area enclosed
                    return -2000; //-Math.pow((n.r || 64), 2) / 64;
                  })
                  .size([width, height])
                  .gravity(0.05 /*0.01*/ /*0.005*/)
                  .linkDistance(function(link, i) {
                    var baseDistance = (link.source.r + link.target.r) * 2;
                    // More siblings => longer link distance
                    var siblings = 0;
                    var srcs = (link.source.links || []).length;
                    var dsts = (link.target.links || []).length;

                    // take larger of the two sibling amounts, capped at 200
                    var siblings = Math.max(srcs, dsts);
                    var distance = (baseDistance) + 10 * (Math.sqrt(siblings + 1));

                    if (link.source.item && link.target.item && link.source.item.state && link.target.item.state) {
                      if (link.source.item.state.hostname !== link.target.item.state.hostname) {
                        distance *= 3;
                      }
                    } else if (link.source.state && link.target.state) {
                      if (link.source.state.hostname !== link.target.state.hostname) {
                        distance *= 3;
                      }
                    }
                    return distance;
                  })
                  .linkStrength(8);

          globalForce = force;

          // Event Function(s)
          var zoom = d3.behavior.zoom()
                      .translate([0, 0])
                      .scale(1)
                      .scaleExtent([0.1, 5])
                      .on("zoom", function () {
                        scope.container.attr("transform", function() {
                            svg.classed("low-zoom", d3.event.scale < 0.5);
                          return 'translate(' + d3.event.translate + ')scale(' + d3.event.scale + ')';
                        });
                      });



          var svg = region.append("svg")
                  .attr("width", "100%")
                  .attr("height","100%")
                  //.style('position', 'absolute')
                  .call(zoom);

          // http://bl.ocks.org/jhb/5955887
          svg.append('defs').append('marker')
              .attr({'id':'arrowhead',
                     'viewBox':'-0 -5 10 10',
                     'refX':10,
                     'orient':'auto',
                     'markerWidth':10,
                     'markerHeight':10,
                     'xoverflow':'visible'})
              .append('svg:path')
                  .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
                  .attr('fill', '#444')
                  .attr('stroke','#444');

          var container = svg.append('g')
                     .attr('class', 'gcontainer');

            container.append('g').attr('class', 'links');
            container.append('g').attr('class', 'nodes');

          scope.container = container;
          scope.svg = svg;
          scope.force = force;

          function getLinkLine(d) {
            var angle = Math.atan2(-(d.target.y - d.source.y),
                                (d.target.x - d.source.x))
            var cosAngle = Math.cos(angle)
            var sinAngle = Math.sin(angle)
            return {
              'x1' : d.source.x + ((d.source.r)* cosAngle),
              'y1' : d.source.y - ((d.source.r)* sinAngle),
              'x2' : d.target.x - ((d.target.r)* cosAngle),
              'y2' : d.target.y + ((d.target.r)* sinAngle)
            };
          }

          force.on('tick', function() {
            scope.nodeElems.attr('transform', function(n) {
              /*
              n.x = n.x || (40*Math.random());
              n.y = n.y || (40*Math.random())
              n.px = n.px || (40*Math.random());
              n.py = n.py || (40*Math.random());
              */
              return 'translate(' + (n.x || 0) + ' ' + (n.y || 0) + ')'
            });

            scope.linkElems.each(function(d, i) {
              var line = getLinkLine(d)
              d3.select(this)
                .attr("x1", line.x1 || 0)
                .attr("y1", line.y1 || 0)
                .attr("x2", line.x2 || 0)
                .attr("y2", line.y2 || 0)
              })
          })

            zoom.scale(0.5);
            zoom.event(svg);
        }
      };
    });
})();