(function () {
angular.module('cascade').directive('d3Tree', function() {


    return {
        restrict: 'EA',
        /* templateUrl: '/app/tree.html', */ // all content is built by d3
        scope: {
            root: '=',
            transposed: '=?'
            // svg: '=',
            // transposed: '=',
            // width: '=',
            // height: '=',
            // totalNodes: '='
        },
        controller: function($scope, $http) {

          $scope.update = function(source) {

              function click(d) {
                  if (d._children) {
                      d.disabled = false;
                  }

                  if (d.children) {
                      d._children = d.children;
                      d.children = null;
                      d.leaf = true;
                  } else {
                      d.leaf = (d._children == null);
                      d.children = d._children;
                      d._children = null;
                  }
                  $scope.update(d);
              }

              var transposed = $scope.transposed,
                  tree = $scope.d3Tree,
                  root = $scope.root;

              // constants dependent on orientation
              var levelLength = transposed ? 200 : 100;
              var separation = transposed ? 40 : 130;
              var textLength = transposed ? 32 : 16;

              var height = $scope.height;
              var width = $scope.width;


              var levelWidth = [1];
              var childCount = function(level, n) {
                  if (n.children && n.children.length > 0) {
                      if (levelWidth.length <= level + 1) {
                        levelWidth.push(0);
                      }

                      levelWidth[level + 1] += n.children.length;
                      n.children.forEach(function(d) {
                          childCount(level + 1, d);
                      });
                  }
              };
              var height = 0;
              function getHeight(n) {
                if (n.children) {
                    return 1 + Math.max.apply(null, n.children.map(getHeight));
                } else {
                    return 1;
                }

              }
              childCount(0, root);

              var autoHeight = getHeight(root) * levelLength;

              var autoWidth = d3.max(levelWidth) * separation; // 25 pixels per line

              // autoWidth = Math.max(autoWidth, width);

              tree.separation(function(a,b) { return separation; });

              //tree = tree.size([newHeight, viewerWidth]);
              // the tree itself doesn't know how it's drawn, so these were bugs
              // var treeWidth = transposed ? newHeight : newWidth;
              // var treeHeight  = transposed ? newWidth  : newHeight;

              tree.size([autoWidth, autoHeight]);
              root.x = (transposed ? $scope.height : $scope.width)/ 2;

              // Compute the new tree layout
              var nodes = tree.nodes($scope.root).reverse();
              var links = tree.links(nodes);

              var duration = 500;

              // Normalize for fixed-depth
              nodes.forEach(function(d) {
                  d.y = (transposed ? 0 : 50) + d.depth * levelLength;
              });

              var diagonal = d3.svg.diagonal().projection(function(d) {
                  return transposed ? [d.y, d.x] : [d.x, d.y];
              });

              function getDiag(d) {
                  var vector = {x: transposed ? d.y : d.x, y: transposed ? d.x : d.y};
                  return diagonal({source: vector, target: vector});
              }

              function translateNode(d) {
                  var x = transposed ? d.y : d.x,
                      y = transposed ? d.x : d.y;
                  return "translate(" + x + "," + y + ")";
              }

              // Update the nodes
              var node = $scope.svg.selectAll("g.tree-node")
                            .data(nodes, function(d) { return d.id || (d.id = ++($scope.totalNodes)); });

              // Enter any new nodes at the parent's previous position
              var nodeEnter = node.enter().append("g")
                                  .attr("class", function(d) {
                                      classes = "tree-node";
                                      if (d.leaf) { classes += " leaf"; }
                                      if (d.disabled) { classes += " disabled"; }
                                      if (d._children) { classes += " collapsed"; }
                                      return classes;
                                  })
                                  .attr("transform", translateNode(source)) /* function(d) {  return translateNode(source); }) */
                                  .on("click", click);

              nodeEnter.append("circle")
                       .attr("r", 1e-6);

              // add the key
              nodeEnter.append("text")
                       .attr("class", "key")
                       .attr("x", transposed ? 15 : 0)
                       .attr("y", function(d) {
                           return transposed ? -5 : 15;
                       })
                       /*.attr("dy", ".35em")*/
                       .attr("text-anchor", function(d) {
                           return transposed ? "left" : "middle";
                       })
                       .text(function(d) { return d.key + ' (' + d.size + ')'; })
                       .style("fill-opacity", 1e-6);


              // add the value
              nodeEnter.append("text")
                       .attr("class", "value")
                       .attr("x", transposed ? 15 : 0)
                       .attr("y", transposed ?  10 : 30)
                       /*.attr("dy", ".35em")*/
                       .attr("text-anchor", function(d) {
                           return transposed ? "left" : "middle";
                       })
                       .text(function(d) {
                           if (transposed && !d.children) {
                              return d.value;
                           }
                           var val = d.value || '';
                           if (val.length > textLength) {
                               val = val.slice(0, textLength - 2) + "...";
                           }
                           return val;
                        })
                       .style("fill-opacity", 1e-6);


              // add the value as a tooltip
              nodeEnter.append("title").text(function(d) { return d.tooltip || d.value; });

              nodeEnter.on('contextmenu', function(d) {
                  d.disabled = !d.disabled;
                  click(d);
                  d3.event.stopPropagation();
                  d3.event.preventDefault();
              });

              // Transition nodes to their new position
              var nodeUpdate = node.transition()
                                   .duration(duration)
                                   .attr("transform", function(d) { return translateNode(d); })
                                   .attr("class", function(d) {
                                       classes = "tree-node";
                                       if (d.leaf) { classes += " leaf"; }
                                       if (d._children) { classes += " collapsed"; }
                                       if (d.disabled) { classes += " disabled"; }
                                       return classes;
                                   });

              nodeUpdate.select("circle")
                        .attr("r", 10);

              nodeUpdate.selectAll("text.key")
                .attr("x", transposed ? 15 : 0)
                .attr("y", transposed ? -5 : 15)
                /*.attr("dy", ".35em")*/
                .attr("text-anchor", function(d) {
                    return transposed ? "left" : "middle";
                })
                .text(function(d) { return (d.key || 'tree root') + ' (' + d.size + ')'; })
                .style("fill-opacity", 1);

              nodeUpdate.selectAll("text.value")
                .attr("x", transposed ? 15 : 0)
                .attr("y", transposed ?  10 : 30)
                /*.attr("dy", ".35em") */
                .attr("text-anchor", function(d) {
                    return transposed ? (d.children ? "left": "right") : "middle";
                })
                .text(function(d) {
                   if (transposed && !d.children) {
                      return d.value;
                   }
                   var val = d.value || '';
                   if (val.length > textLength) {
                       val = val.slice(0, textLength - 2) + "...";
                   }
                   return val;
                 })
                .style("fill-opacity", 1);

              nodeUpdate.selectAll("text")
                        .style("fill-opacity", 1);

              // Transition exiting nodes to the parent's new position
              var nodeExit = node.exit().transition()
                                 .duration(duration)
                                 .attr("transform", translateNode(source))
                                 .remove();

              nodeExit.select("circle")
                      .attr("r", 1e-6);

              nodeExit.selectAll("text")
                      .style("fill-opacity", 1e-6);

              // Update the links
              var link = $scope.svg.selectAll("path.link")
                            .data(links, function(d) { return d.target.id; });

              // Enter any new links at the parent's previous position
              link.enter().insert("path", "g")
                  .attr("class", "link")
                  .attr("d", function(d) { return getDiag(source);});

              // Transition links to their new position
              link.transition()
                  .duration(duration)
                  .attr("d", diagonal);

              // Transition exiting nodes to the parent's new position
              link.exit().transition()
                  .duration(duration)
                  .attr("d", function(d) { return getDiag(source);})
                  .remove();

          }
          // if anything changes, re-draw the whole tree
          $scope.$watch(function() {
              $scope.update($scope.root);
          });

        },
        link: function($scope, elem, attributes) {

            // var root = $scope.root;
            $scope.height = elem[0].offsetHeight;
            $scope.width = elem[0].offsetWidth;
            var region = d3.select(elem[0])
                             .attr("class", "rounded height-full")
                             .style("border-style", "solid")
                             .style("border-width", 1);

            $scope.d3Tree = d3.layout.tree().size([$scope.width, $scope.height])
            $scope.baseSvg = region.append('svg')
                                 .attr('height', $scope.height)
                                 .attr('width', $scope.width);
            $scope.svg = $scope.baseSvg.append('g');

            // $scope.transposed = false;
            $scope.totalNodes = 0;
            $scope.root = $scope.root  || {};


            // Define the zoom function for the zoomable tree
            function zoom() {
                $scope.svg.attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")");
            }


            // define the zoomListener which calls the zoom function on the "zoom" event constrained within the scaleExtents
            $scope.zoomListener = d3.behavior.zoom().scaleExtent([0.01, 5]).on("zoom", zoom);
            $scope.baseSvg.call($scope.zoomListener);
            // this will get called automatically whenever it changes with $scope.$watch
            //$scope.update($scope.root);
        }
    };
  });
})();
