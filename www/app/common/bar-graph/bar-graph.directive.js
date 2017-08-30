(function() {
    angular.module('cascade').directive("barGraph", function() {
      var GRAPH_WIDTH = 960, GRAPH_HEIGHT = 500;

      function constructBarGraph(svg, data) {
        var margin = {top: 20, right: 20, bottom: 30, left: 40},
            width = GRAPH_WIDTH - margin.left - margin.right,
            height = GRAPH_HEIGHT - margin.top - margin.bottom;

        var x = d3.scale.ordinal()
            .rangeRoundBands([0, width], .1);

        var y = d3.scale.linear()
            .range([height, 0]);

        var xAxis = d3.svg.axis()
            .scale(x)
            .orient("bottom");

        var yAxis = d3.svg.axis()
            .scale(y)
            .orient("left")
            .ticks(10);

        svg.attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)

        svgGroup = svg.append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");


        x.domain(data.map(function(d) { return d.tactic; }));
        y.domain([0, d3.max(data, function(d) { return d.count; })]);

        svgGroup.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + height + ")")
            .call(xAxis);

        svgGroup.append("g")
            .attr("class", "y axis")
            .call(yAxis)
          .append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", 6)
            .attr("dy", ".71em")
            .style("text-anchor", "end")
            .text("Count");

        svgGroup.selectAll(".bar")
            .data(data)
          .enter().append("rect")
            .attr("class", "bar")
            .attr("x", function(d) { return x(d.tactic); })
            .attr("width", x.rangeBand())
            .attr("y", function(d) { return y(d.count); })
            .attr("height", function(d) { return height - y(d.count); });
      }

      return {
        restrict: 'A',
        scope: {
          tactics: "="
        },
        controller: function($scope, $window) {
          console.log("bar controller");
          $scope.$watch(function() {
            if ($scope.tactics) {
              constructBarGraph($scope.svg, $scope.tactics);
            }
          });
        },
        link: function(scope, elem, attrs) {
          console.log("bar link");
          scope.svg = d3.select(elem[0]).append('svg');
        }
      }
    });
})();