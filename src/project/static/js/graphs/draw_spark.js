/*
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
*/

function create_project_activity(project) {
console.log(project)
width = d3.select("#project_activity_"+project).node().getBoundingClientRect().width
height = width*0.2

var parseDate = d3.timeParse("%Y-%m-%d")

var x = d3.scaleTime()
	    .range([0, width]);

var y = d3.scaleLinear()
	.range([height, 0]);

var area = d3.area()
	.curve(d3.curveBasis)
    .x(function(d) { return x(d.datum); })
    .y1(function(d) { return y(d.val); });

var valueline = d3.line()
	.curve(d3.curveBasis)
    //.defined(function(d) { return d.val != 0; })
		.x(function(d) { return x(d.datum); })
    .y(function(d) { return y(d.val); });

var svg = d3.select("#project_activity_"+project).append("svg")
    .attr("width", width)
    .attr("height", height)
  .append("g")
   .attr("transform", "translate(" + 0 + "," + 0 + ")");


d3.json("/timelog/api/project_activity/?project="+project, function(error, data) {
	if (error) throw error;
	delete data[0]
	data.splice(0,1)
	console.log(data)
	data.forEach(function(d) {
		d.datum = parseDate(d.datum);
	});

	x.domain(d3.extent(data, function(d) { return d.datum; }));
	y.domain([0, d3.max(data, function(d) { return d.val; })]);
    area.y0(y(0));
	svg.append("path")
	       .datum(data)
	       .attr("class", "area")
           .attr("fill", "#00e5ff")
	       .attr("d", area);
  // Add the valueline paPth.
 svg.append("path")
      .datum(data)
      .attr("fill", "none")
      .attr("stroke", "#00e5ff")
      .attr("stroke-linejoin", "round")
      .attr("stroke-linecap", "round")
      .attr("stroke-width", 1.5)
      .attr("d", valueline);


});
}
