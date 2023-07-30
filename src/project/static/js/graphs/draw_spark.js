/*
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin, Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under BSD-2-Clause License.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
   2. Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer
      in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
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
