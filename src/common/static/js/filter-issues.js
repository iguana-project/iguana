/*
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
*/
function filter_issues(base_class_name) {
	var input = document.getElementById('text-filter');
	var filter = input.value.toUpperCase();
	var issues = document.getElementsByClassName(base_class_name);

	for (var i = 0; i < issues.length; i++) {
		var issue_text = "";

		var ids = issues[i].getElementsByClassName('issue-id-link');
		for (var j = 0; j < ids.length; j++) {
			issue_text += " " + ids[j].innerHTML;
		}

		var titles = issues[i].getElementsByClassName('issue-title');
		for (var j = 0; j < titles.length; j++) {
			issue_text += " " + titles[j].innerHTML;
		}

		var tags = issues[i].getElementsByClassName('issue-tag');
		for (var j = 0; j < tags.length; j++) {
			issue_text += " " + tags[j].innerHTML;
		}

		issue_text += " "
		if (issue_text.toUpperCase().indexOf(filter) > -1) {
			issues[i].style.display = "";
		} else {
			issues[i].style.display = "none";
		}
	}
}
