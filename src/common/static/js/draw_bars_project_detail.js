/*
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
*/
var counter = 0;
var svg, proj;
var curr;
var data_type;
function draw(data) {
	var formatdate = d3.timeFormat("%d.%m");
	var margin = {top: 0, right: 5, bottom: 18, left: 5},
		width = d3.select("#project_activity").node().getBoundingClientRect().width
	width = width - margin.left - margin.right,
		height = width*0.3 - margin.top - margin.bottom;

	// set the ranges
	var x = d3.scaleBand()
		.range([0, width])
		.padding(0.1)

	var y = d3.scaleLinear()
		.range([height, 0]);

	var tooltip = d3.select("body")
		.append("div")
		.style("position", "absolute")
		.style("z-index", "10")
		.style("visibility", "hidden")
		.text("a simple tooltip");

	// append the svg object to the body of the page
	// append a 'group' element to 'svg'
	// moves the 'group' element to the top left margin
	d3.select("svg").remove();
	svg = d3.select("#project_activity").append("svg")
		.attr("width", width + margin.left + margin.right)
		.attr("height", height + margin.top + margin.bottom)
		.append("g")
		.attr("transform",
			"translate(" + margin.left + "," + margin.top + ")");

	// Scale the range of the data in the domains
	x.domain(data.map(function(d) { return d.datum; }));
	y.domain([0, d3.max(data, function(d) { return d.val; })]);

	// append the rectangles for the bar chart
	svg.selectAll(".bar")
		.data(data)
		.enter().append("rect")
		.attr("class", "bar")
		.attr("x", function(d) { return x(d.datum); })
		.attr("width", x.bandwidth())
		.attr("y", function(d) { return y(d.val); })
		.attr("height", function(d) { return height - y(d.val); })
		.on("mouseover", function(d){
			if (data_type === 'timelog') {
				tooltip.text(Math.round(d.val*10/3600)/10 + " hours");
			} else if (data_type === 'actions') {
				if (d.val === 1)
					tooltip.text(d.val + " action");
				else
					tooltip.text(d.val + " actions");
			}
			return tooltip.style("visibility", "visible");})
		.on("mousemove", function(){return tooltip.style("top", (d3.event.pageY-20)+"px").style("left",(d3.event.pageX+10)+"px");})
		.on("mouseout", function(){return tooltip.style("visibility", "hidden");});
	// add the x Axis
	svg.append("g")
		.attr("transform", "translate(0," + height + ")")
		.call(d3.axisBottom(x)
			.tickValues(x.domain().filter(function(d,i){ return !(i%3)}))
			.tickFormat(function(d) { return formatdate(d);})
			.tickSizeOuter(0)
		);
}

function create_project_activity(project, delta=0) {
	proj=project;
	var parseDate = d3.timeParse("%Y-%m-%d")
	d3.json("/timelog/api/project_activity/?project="+project+"&delta="+delta, function(error, data) {
		if (error) throw error;
		data_type = data[0]['data']
		data.splice(0,1)
		data.forEach(function(d) {
			d.datum = parseDate(d.datum);
		});
		draw(data);
	});
}


$( document ).ready(function() {
	$("#project-detail-previous-day").on( "click", function () {
		if(counter === 0)
			$( "#project-detail-next-day" ).removeClass( "disabled" )
		$( "#project-detail-next-week" ).removeClass( "disabled" )
		counter++;
		create_project_activity(proj, counter);
	});
	$("#project-detail-previous-week").on( "click", function() {
		if(counter === 0)
			$( "#project-detail-next-day" ).removeClass("disabled")
		$( "#project-detail-next-week" ).removeClass("disabled")
		counter += 7;
		create_project_activity(proj, counter);
	});
	$( "#project-detail-next-day" ).click(function() {
		if($( "#project-detail-next-day" ).hasClass("disabled"))
			return;
		if(counter === 1) {
			$( "#project-detail-next-day" ).addClass("disabled")
			$( "#project-detail-next-week" ).addClass("disabled")
		}
		counter--;
		create_project_activity(proj, counter);
	});

	$( "#project-detail-next-week" ).click(function() {
		if($( "#project-detail-next-week" ).hasClass( "disabled" ))
			return;
		if(counter <= 7) {
			$( "#project-detail-next-day" ).addClass( "disabled")
			$( "#project-detail-next-week" ).addClass( "disabled" )
			counter = 0;
		} else {
			counter -=7
		}
		create_project_activity(proj, counter);
	});
});
