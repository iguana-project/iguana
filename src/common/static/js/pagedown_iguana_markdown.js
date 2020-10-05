(function () {
    var markdown, original_getSanitizingConverter,
        extra_markdown, original_extraInit;
    if (typeof exports === "object" && typeof require === "function") { // we're in a CommonJS (e.g. Node.js) module
        markdown = exports;
        original_getSanitizingConverter = require("./Markdown.Sanitizer").getSanitizingConverter;

        extra_markdown = require("./Markdown.Extra");
        original_extraInit = extra_markdown.init;
    } else {
        markdown = window.Markdown;
        original_getSanitizingConverter = markdown.getSanitizingConverter;

        extra_markdown = markdown.Extra;
        original_extraInit = extra_markdown.init;
    }

    // override getSanitizingConverter function from Markdown.Sanitizer to add more hooks to Markdown.Converter
    markdown.getSanitizingConverter = function () {
        var converter = original_getSanitizingConverter();
        converter.hooks.chain("preConversion", includeUser);
        converter.hooks.chain("preConversion", includeIssue);
        converter.hooks.chain("preSpanGamut", escapePseudoTags);
        converter.hooks.chain("postConversion", includeIns); // postSpanGamut does not work here since the <ins> tag is not in 'basic_tag_whitelist' variable of Markdown.Sanitizer.js
        return converter;
    }

    // override init function from Markdown.Extra to specify the extra options
    extra_markdown.init = function(converter, _options) {
        return original_extraInit(converter, {
            extensions: ["tables", "fenced_code_gfm", "footnotes", "newlines", "strikethrough"]
        });
    }

    // helper function for getting JSON variables from the Django json_script filter
    function getVariableById(id) {
        el = document.getElementById(id)
        if(el === null) {
            return null;
        }

        return JSON.parse(el.textContent)
    }

    // match any user name in the markdown text and replace it with a link to that user
    function includeUser(text) {
        var userData = getVariableById("user_markdown_data");
        if(userData === null){
            return text;
        }

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
        if(issueData === null){
            return text;
        }

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

    // add the <ins> tag for '++'
    function includeIns(text) {
        // pattern nearly the same as _DoItalicsAndBold
        return text.replace(/([\W_]|^)(\+\+)(?=\S)([^\r]*?\S[\+]*)\2([\W_]|$)/g,
            "$1<ins>$3</ins>$4");
    }

    function escapePseudoTags(text) {
        // copied from Markdown.Sanitizer (added 'a', 'img' and 'ins' tag)
        var basic_tag_whitelist = /^(<\/?(a|b|blockquote|code|del|dd|dl|dt|em|h1|h2|h3|i|img|ins|kbd|li|ol(?: start="\d+")?|p|pre|s|sup|sub|strong|strike|ul)>|<(br|hr)\s?\/?>)$/i;

        return text.replace(/<[^>]*>?/gi, function(tag) {
            // check if tag is in white list
            if (tag.match(basic_tag_whitelist))
                // if so, just return it
                return tag;
            else {
                // escape the angle brackets
                tag = tag.replace(/</g, "&lt;");
                return tag.replace(/>/g, "&gt;");
            }
        });
    }
})();


(function () {
    // get the current line break character
    if (navigator.appVersion.indexOf("Win")!=-1){
        var os_linebreak = "\r\n";
    } else {
        var os_linebreak = "\n";   
    }

    var wmd_editors = document.getElementsByClassName("wmd-input");
    for (i = 0; i < wmd_editors.length; i++) {
        wmd_editors[i].addEventListener('keydown', function(e) {
            var keyCode = e.keyCode || e.which;

            // the tab key is '9'
            if (keyCode == 9) {
                e.preventDefault();

                var start = this.selectionStart;
                var end = this.selectionEnd;

                var string_before = $(this).val().substring(0, start);
                // the default amount of spaces is '4'
                var default_space_amount = 4
                // calculate the amount of spaces that should be added
                var space_amount = default_space_amount - (
                                                           // only consider the current line
                                                           // so get the index of the current line
                                                           (start - (string_before.lastIndexOf(os_linebreak) + 1))
                                                           // get the modulo to the default space amount
                                                           % default_space_amount);

                // set textarea value to: text before caret + spaces + text after caret
                $(this).val(string_before
                            + " ".repeat(space_amount)
                            + $(this).val().substring(end));

                // put caret at right position again
                this.selectionStart = this.selectionEnd = start + space_amount;
            }
        });
    }
})();
