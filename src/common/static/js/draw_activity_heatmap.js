/*
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
*/
function draw_activity_heatmap(username, advanced, data_param) {

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
project = findGetParameter('project')
data_type = data_param || findGetParameter('data')
api_url = '/timelog/api/activity/'

d3.json(api_url+"?project="+project+"&user="+username+"&data="+data_type, function(error, data) {
	var cal;
	var datum = new Date()
	datum.setDate(5)
	datum.setMonth(datum.getMonth()+1)
	datum.setFullYear(datum.getFullYear()-1)
	var start = datum
	var user = data.USERNAME
	var max = data.MAXIMUM
	delete data.MAXIMUM
	delete data.START_MONTH
	delete data.USERNAME
	var logs_on_this_day = []
	var parseTime = d3.time.format("%H:%M:%S").parse;
	var parseDate = d3.time.format.utc("%Y-%m-%dT%H:%M:%S.%LZ").parse;
	var formatDate = d3.time.format("%Y-%m-%d %H:%M:%S");
	function pad(n) {
		return (n < 10) ? ("0" + n) : n;
	}

	var responsiveCal = function( options ) {
		size = $('#cal-heatmap').parent().width()
		if( $(window).width() < 1200 ) {
			options.colLimit = Math.round(size/180)
			options.domainLabelFormat= "%m"
		} else {
			delete options.colLimit;
			options.colLimit = Math.round(size/160)
			delete options.domainLabelFormat;
		}
		if(cal) {
			$('#cal-heatmap').html('');
			cal.destroy()
		}
		cal = new CalHeatMap();
	        cal.init( options );
		cal.setLegend([Math.round(max/16),Math.round(max/8),Math.round(max/4),Math.round(max/2)])
	}

	caloptions = {
		start: new Date(start), // January, 1st 2000
		range: 12,
		itemSelector: "#cal-heatmap",
		previousSelector: "#cal-heatmap-previous",
		nextSelector: "#cal-heatmap-next",
		domain: "month",
		subDomain: "day",
		data: data,
		dataType: "json",
		tooltip: true,
		onClick: function(date, nb) {
			if (!advanced || data_type === 'actions')
				return;
			$("#onClick-placeholder").html("").css("visibility", "visible")
			var myKeys = Object.keys(data)
			var datestring = date.getFullYear().toString() + pad(date.getMonth()+1) + pad(date.getDate())
			d3.json("/timelog/api/"+datestring+"?project="+project, function(error, data) {
				logs_on_this_day = data;
				$("#onClick-placeholder").append("");
					$("#onClick-placeholder").append('<ul id="loglist" class="list-group">');
				if ( logs_on_this_day.length === 0) {
					$("#loglist").append('<li class="list-group-item" id="elem0">');
					$("#elem0").append("no logs on this day");
					$("#onClick-placeholder").append("</li></ul>");
				}
				var i = 0;
				data.forEach( function(d) {
					var days = d.fields.time.split(" ");
					if (days.length > 1) {
						var day = days[0]
						var times = days[1]
					} else {
						var day = "0"
						var times = days[0]
					}
					var time = times.split(":");

					var str ='<li id="listelement' + i.toString() + '" class="list-group-item listelement' + i.toString() +'">'
					$("#loglist").append(str);

					var sel = '.listelement' + i.toString()
					if (parseInt(day)>0)
						$(sel).append(parseInt(day) + "d")
					if (parseInt(time[0])>0)
						$(sel).append(parseInt(time[0]) + "h");
					if (parseInt(time[1])>0)
						$(sel).append(parseInt(time[1]) + "m");
					$(sel).append(" on Issue <a href=\"" + d.fields.issue_url +"\">" + d.fields.issue_short + "</a>"
								+" in Project <a href=\""+ d.fields.issue_proj_url +"\">" + d.fields.issue_project_name + "</a></p>"
					);
					$(sel).append("<small>"+formatDate(parseDate(d.fields.created_at))+"</small>");

				i = i+1;

				});
				$("#onClick-placeholder").append("</ul>");
			});
		}
	};

	// run first time, put in load if your scripts are in footer
	if (data_type === 'actions')
		caloptions.itemName =  ["action","actions"]
	else
		caloptions.itemName =  ["minute","minutes"]
	responsiveCal( caloptions );

	$(window).resize(function() {
		    if(this.resizeTO) clearTimeout(this.resizeTO);
		        this.resizeTO = setTimeout(function() {
				        $(this).trigger('resizeEnd');
				    }, 500);
	});
	$(window).bind("resizeEnd", function() {
		    // run on resize
			responsiveCal( cal.options );

	});
});
};
