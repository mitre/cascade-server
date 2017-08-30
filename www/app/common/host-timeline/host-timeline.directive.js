angular.module('cascade').directive("hostTimeline", function() {
  return {
    restrict: 'AE',
    templateUrl: "/app/common/host-timeline/host-timeline.html",
    scope: {
      events: "="
    },
    controller: function($scope, $window, $element) {
      // TODO: move this to link
      /*
      $(window).on('resize', function() {
        redraw();
        $scope.$apply();
      });
      */

      function redraw() {
          if ($scope.events && $scope.events.length) {
          d3.select("#hosts-chart").selectAll("*").remove();
          constructChart($scope);
          }
      }

      //$(window).on('resize', redraw);
      $scope.$watch(function () {
            return [$window.innerWidth, $window.innerHeight, $element[0].offsetWidth, $element[0].offsetHeight, $element.css('display')].join('x');
          },
          redraw);
      $scope.$watchGroup(['events', 'events.length'], redraw);

      function constructChart() {
        var events = _.sortBy($scope.events, 'time');

        function getHostKey(e) {
          return (e.state.fqdn || e.state.hostname || "").split(".")[0].toUpperCase();
        }

        var eventMapping = {}
        for (var i = 0; i < events.length; i++) {
          eventMapping[events[i]._id] = events[i];
        }

        var eventIndices = {}
        for (var i = 0; i < events.length; i++) {
          eventIndices[events[i]._id] = i;
        }

        var links = []
        for (var i = 0; i < events.length; i++) {
          for (var j = 0; j < events[i].links.length; j++) {
            var dest = eventMapping[events[i].links[j]];
            if (dest && (getHostKey(events[i]) != getHostKey(dest))) {
              links.push({"source": i, "target" : eventIndices[dest._id]});
            }
          }
        }

        var lateralMoveEvents = new Set();
        for (var i = 0; i < links.length; i++) {
          lateralMoveEvents.add(events[links[i].source]._id);
          lateralMoveEvents.add(events[links[i].target]._id);
        }

        var hosts = Array.from(new Set(events.map(d => getHostKey(d))));
        var hostIndices = {};
        for (var i = 0; i < hosts.length; i++) {
            hostIndices[hosts[i]] = i;
        }

        var getColor = function() {
          var colors = d3.scale.category10();
          return i => colors(i%10);
        }();

        function getHostY(h) {
          return hostHeight*hostIndices[h] + hostHeight/2;
        }

        function getEventY(e) {
          return getHostY(getHostKey(e))
        }

        function getEventDate(e) {
          return new Date(e.time);
        }

        function createTooltip(n) {
          var tooltip = [];
          for (var key in n) {
            if (key ==='links'|| key==='reverse_links' || key === 'metadata') {
              continue;
            }
            var val = n[key];
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
        }

        function minimum(arr) {
            return arr.reduce((a,b) => a < b ? a : b);
        }

        function maximum(arr) {
            return arr.reduce((a,b) => a > b ? a : b);
        }

        var axisHeight = Math.max($('#hosts-chart').height(), 480),
            height = axisHeight * hosts.length / (hosts.length + 1),
            hostHeight = height / hosts.length,
            labelsWidth = 175,
            width = Math.max($('#hosts-chart').width(), 720) - labelsWidth - 50,
            nodeRadius = 7.5,
            labelBuffer = 10,
            xScale = d3.time.scale()
              .range([0, width]),
            xAxis = d3.svg.axis()
              .scale(xScale)
              .orient("bottom")
              .tickSize(5, 5)
              .tickPadding(6);

        {
          var eventTimes = events.map(getEventDate);
          var minDate = minimum(eventTimes);
          var maxDate = maximum(eventTimes);
          var dateBuffer = 0.10*(maxDate - minDate); // buffer each side with 10% of the full range
          xScale.domain([new Date(minDate.getTime() - dateBuffer) , new Date(maxDate.getTime() + dateBuffer)]);
        }

        var svg = d3.select("#hosts-chart").append("svg")
          .attr("width", "100%")
          .attr("height", "100%");

        var chart = svg.append("g")
          .attr("transform", "translate(" + labelsWidth + ",0)");

        chart.append("g")
          .attr("class", "x axis")
          .attr("transform", "translate(0," + height + ")");

        var zoom = d3.behavior.zoom()
          .x(xScale)
          .scaleExtent([0.5, Infinity])
          .on("zoom", drawChart);

        chart.append("rect")
          .attr("class", "pane")
          .attr("width", width)
          .attr("height", height)
          .call(zoom);

        svg.append("rect")
          .attr("x", 0)
          .attr("y", 0)
          .attr("width", labelsWidth)
          .attr("height", height)
          .style("fill", "white");

        svg.selectAll("text.host").data(hosts)
          .enter().append("text").attr("class", "host")
            .text(h => h)
            .attr("x", labelsWidth - labelBuffer)
            .attr("y", getHostY)
            .attr("dy", "0.35em") // vertically center text
            .attr("text-anchor", "end");

        chart.selectAll("line.host").data(hosts)
          .enter().append("line").attr("class", "host")
            .attr("x1", 0)
            .attr("y1", d => getHostY(d))
            .attr("x2", width)
            .attr("y2", d => getHostY(d));

        svg.append('defs').append('marker')
            .attr({'id':'arrowhead',
                   'viewBox':'-0 -5 10 10',
                   'refX': 10 + nodeRadius*2,
                   'orient':'auto',
                   'markerWidth': 5,
                   'markerHeight': 5,
                   'xoverflow':'visible'})
            .append('svg:path')
                .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
                .attr('fill', '#000')
                .attr('stroke','#000');


        var lateralMove = d3.select("#hosts-lateralmove");
        lateralMove.on("click", function() {
          drawChart();
        });

        chart.append("text").attr("class", "daterange")
          .attr("id", "hosts-startdate")
          .attr("x", 0)
          .attr("y", height)
          .attr("dy", -3);

        chart.append("text").attr("class", "daterange")
          .attr("id", "hosts-enddate")
          .attr("x", width)
          .attr("y", height)
          .attr("dy", -3)
          .attr("text-anchor", "end");

        var axisDateFormat = d3.time.format("%d %b %Y");

        function drawChart() {
          chart.select("g.x.axis").call(xAxis);
          chart.select("#hosts-startdate")
            .text(axisDateFormat(xScale.domain()[0]));
          chart.select("#hosts-enddate")
            .text(axisDateFormat(xScale.domain()[1]));

          var lines = chart.selectAll("line.link").data(links);
          lines.enter().append("line").attr("class", "link")
          lines
            .attr("x1", d => xScale(getEventDate(events[d.source])))
            .attr("y1", d => getEventY(events[d.source]))
            .attr("x2", d => xScale(getEventDate(events[d.target])))
            .attr("y2", d => getEventY(events[d.target]))

          var circles = chart.selectAll("circle.node")
            .data(events);
          circles.enter().append("circle").attr("class", "node")
            .style("stroke", "black")
            .attr("r", nodeRadius)
            .style("fill", d => getColor(hostIndices[getHostKey(d)]))
            .call(zoom) // allows zoom to work even when cursor is on a circle
            .append("title")
              .text(d => createTooltip(d));
          circles
            .attr("cx", d => xScale(getEventDate(d)))
            .attr("cy", getEventY)
            .style("visibility", function(d) {
              if (lateralMove.property('checked') && !lateralMoveEvents.has(d._id)) {
                return "hidden";
              }
              else {
                return "visible";
              }
            });
        }
        drawChart();
      }

    }
  }

});
