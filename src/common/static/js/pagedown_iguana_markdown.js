(function () {
    var output, original_getSanitizingConverter;
    if (typeof exports === "object" && typeof require === "function") { // we're in a CommonJS (e.g. Node.js) module
        output = exports;
        original_getSanitizingConverter = require("./Markdown.Sanitizer").getSanitizingConverter;
    } else {
        output = window.Markdown;
        original_getSanitizingConverter = output.getSanitizingConverter;
    }

    // override getSanitizingConverter function from Markdown.Sanitizer to add more hooks to Markdown.Converter
    output.getSanitizingConverter = function () {
        var converter = original_getSanitizingConverter();
        converter.hooks.chain("preConversion", includeUser);
        converter.hooks.chain("preConversion", includeIssue);
        return converter;
    }

    // helper function for getting JSON variables from the Django json_script filter
    function getVariableById(id) {
        el = document.getElementById(id)
        if(el === null) {
            return "";
        }

        return JSON.parse(el.textContent)
    }

    // match any user name in the markdown text and replace it with a link to that user
    function includeUser(text) {
        var userData = getVariableById("user_markdown_data");
        var re = new RegExp(userData.re_pattern, "g");
        return text.replace(re, function(match, userName) {
            var userUrl = userData.user_url;
            userUrl = userUrl.replace("<user_name>", userName.substr(1));
            return "[" + userName + "](" + userUrl + ")";
        });
    }

    // match any issue in the markdown text and replace it with a link to it
    function includeIssue(text) {
        var issueData = getVariableById("issue_markdown_data");
        var re = new RegExp(issueData.re_pattern, "g");
        var maxTicketNumber = parseInt(issueData.max_ticket_number, 10);
        return text.replace(re, function(match, issueName) {
            var curTicketNumber = parseInt(issueName.split('-')[1], 10);
            if(curTicketNumber <= 0 || curTicketNumber > maxTicketNumber) {
                return issueName;
            }

            var issueUrl = issueData.issue_url;
            issueUrl = issueUrl.replace("<issue_number>", curTicketNumber.toString(10));
            return "[" + issueName + "](" + issueUrl + ")";
        });
    }
})();
