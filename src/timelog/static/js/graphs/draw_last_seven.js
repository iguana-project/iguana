/*
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
*/
var counter = 0;
function draw(){
	var Chart = (function(window,d3) {

		var parseDate = d3.utcParse("%Y-%m-%dT%H:%M:%S.%LZ");
		var formatDate = d3.timeFormat("%Y-%m-%d");
		var parseTime = d3.timeParse("%H:%M:%S");

		var data, height, width, margin = {}, grouped_by_date = [], x_domain = [], color, x, y;
		function findGetParameter(parameterName) {
			var result = "";
			var tmp = [];
			location.search
				.substr(1)
				.split("&")
				.forEach(function (item) {
					tmp = item.split("=");
					if (tmp[0] === parameterName) result = decodeURIComponent(tmp[1]);
				});
			return result;
		}

		d3.json('/timelog/api/last_7_days/'+'?project='+findGetParameter('project'), init);

		function init(error, data) {
			data = data;
			data.forEach(function(d) {
				d.fields.created_at = parseDate(d.fields.created_at)
				d.fields.created_at = formatDate(d.fields.created_at)
				var x = parseTime(d.fields.time)
				if (!x) {
					var days = d.fields.time.split(" ")
					var rest = parseTime(days[1])
					d.fields.time = parseInt(days[0])*24*60 + rest.getHours()*60 + rest.getMinutes()
				} else {
					d.fields.time = x.getHours()*60 + x.getMinutes()
				}
			});

			var res = [];
			data.forEach(function(entry) {
				res.push(entry.fields)
			});

			grouped_by_date = d3.nest()
				.key(function(d) { return d.created_at; })
				.entries(res);

			// add missing days
			var currentdate = new Date();

			for(var i=6; i>=0; i--) {
				x_domain.unshift(formatDate(currentdate));
				var a = grouped_by_date.find(x => x.key === formatDate(currentdate))
				if (typeof a === 'undefined' || !a) {
					var object={};
					object.key = formatDate(currentdate);
					var values = [];
					object.values = values;
					grouped_by_date.push(object)
				};
				currentdate.setDate(currentdate.getDate() - 1);
			}
			color = d3.scaleOrdinal(d3.schemeCategory20);

			grouped_by_date.sort(function(a, b){
				if(a.key < b.key) {
					return -1;
				} else if (a.key > b.key){
					return +1;
				} else {
					return 0;
				}
			});

			if(grouped_by_date.length === 8)
				grouped_by_date.shift()

			render();
		}


		function render() {


			updateDimensions(window.innerWidth, window.innerHeight);

			x = d3.scaleBand().range([0, width - margin.left - margin.right]);
			y = d3.scaleLinear().range([height - margin.top - margin.bottom, 0]);


			var max_per_day=0;

			x.domain(x_domain);

			y.domain([0,
				d3.max(grouped_by_date,
					function(d) { var res=0; var temp=0;
						d.values.forEach(function(e) {res=res+e.time; temp++;});
						if(temp>max_per_day) max_per_day=temp; return res;})
				+ 50
			]
			);

			for(var j=0; j<7; j++) {
				var k=0;
				grouped_by_date[j]["colors"] = [];
				for(var i=0; i<grouped_by_date[j].values.length; i++){
					grouped_by_date[j]["id_"+i] = grouped_by_date[j].values[i].time
					grouped_by_date[j]["colors"].push(color(grouped_by_date[j].values[i].issue))
					k++;
				}
				while(k<max_per_day) {
					grouped_by_date[j]["id_"+k] = 0
					grouped_by_date[j]["colors"].push(color(k))
					k++;
				}
			}

			keys = [];
			for (var i=0; i<max_per_day; i++) {
				keys.push("id_"+i);
			}

			var stack = d3.stack()
				.keys(keys)
				.value(function(d, key) { return d[key]; })
				.order(d3.stackOrderNone)
				.offset(d3.stackOffsetNone);

			var series = stack(grouped_by_date);

			var svg = d3.select("body").select("div#chart_last_seven").append("svg")
				.attr("width", width + margin.left + margin.right)
				.attr("height", height + margin.top + margin.bottom)
				.append("g")
				.attr("transform","translate(" + margin.left + "," + margin.top + ")");

			var layer = svg.selectAll(".layer")
				.data(series)
				.enter().append("g")
				.attr("class", "layer")

			layer.selectAll("rect")
				.data(function(d) { return d; })
				.enter().append("rect")
				.attr("x", function(d) { return x(d.data.key); })
				.attr("y", function(d) { return y(d[1]); })
				.attr("height", function(d) { return y(d[0]) - y(d[1]); })
				.attr("width", x.bandwidth())
				.style("stroke", "#000000")
				.style("stroke-width", 1)
				.style("fill", function(d, i) {return d.data["colors"].shift(); });

			svg.selectAll("rect")
				.on("mousemove", function(d, i) {
					var idx = Math.floor(i/7);       
					console.log(this.getBoundingClientRect().height); 
					console.log(this.getBoundingClientRect().bottom); 
					console.log(this.getBoundingClientRect().top); 
					var y = this.getBoundingClientRect().top + window.scrollY-10;
					var x = this.getBoundingClientRect().left
					tooltip
						.style("left", x-120/2 + "px")
						.style("top",  y+ "px" )
						.style("display", "inline-block")
						.style("-webkit-transform", "translateY(-100%)")
						.style("-moz-transform", "translateY(-100%)")
						.html("Issue: " + d.data.values[idx].issue_short + "<br>"
							+ "Project: " + d.data.values[idx].issue_project_name
							+ "<br>" + "<b>"+(d[1]-d[0]).toString()+"</b>" + " Minutes");
				})
				.on("mouseout", function(d){ tooltip.style("display", "none");})

				.on("dblclick", function (d,i) {
					var idx = Math.floor(i/7)
					window.location = d.data.values[idx].issue_url
				});

			var tooltip = d3.select("body").append("div").attr("class", "ch-tooltip");


			svg.append("g")
				.attr("id", "xaxis")
				.attr("class", "x axis")
				.attr("transform", "translate(0," + (height - margin.top - margin.bottom) + ")")
				.call(d3.axisBottom(x)
					.tickValues([x_domain[0], x_domain[2], x_domain[4], x_domain[6]])
					.tickSizeOuter(0)
				);

			svg.append("g")
				.call(d3.axisLeft(y).tickSizeOuter(0));

			svg.append("text")
				.attr("transform", "rotate(-90)")
				.attr("y", 0 - margin.left)
				.attr("x",0 - (height / 2))
				.attr("dy", "1em")
				.style("text-anchor", "middle")
				.text("Minutes");

		};

		function updateDimensions(winWidth, winHeight) {
			d3.select("svg").remove();
			margin.top = 20;
			margin.right = 0;
			margin.left = 50;
			margin.bottom = 20;
			var divwidth = parseFloat(d3.select("#chart_last_seven").style("width"))
			width = (divwidth - margin.left - margin.right);
			height = 0.7 * width;
		}

		return {
			render : render
		}




	})(window,d3);
	window.addEventListener('resize', Chart.render);
}
draw();

