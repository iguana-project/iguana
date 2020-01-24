(function () {
    var output, tribute;
    if (typeof exports === "object" && typeof require === "function") { // we're in a CommonJS (e.g. Node.js) module
        output = exports;
        tribute = require("./tribute.min");
    } else {
        output = window
        tribute = window.Tribute;
    }
    
    
    window.TributeWrapper = class TributeWrapper {
        defaultCollection = {
            containerClass: 'dropdown-menu-autocomplete',
            trigger: '',
            values: '',
            selectTemplate: '',
            menuItemTemplate: function (item) {
                var enabled = ""
                if("selectable" in item.original && !item.original.selectable)
                    enabled = 'class="disabled"';
                return '<a href="#" ' + enabled + '>' + item.original.text +"</a>";
            },
            lookup: "cleaned_text",
            fillAttr: "cleaned_text",
            searchOpts: {
                pre: '',
                post: '',
                skip: true,
            },
        };
        collections = [];
        tributeObject = null;
        
        
        remoteSearch(text, queryURL, cb) {
            var that = this;
            var xhr = new XMLHttpRequest();
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        var data = JSON.parse(xhr.responseText);
                        cb(data.results);
                    } else {
                        cb([]);
                    }
                } else {
                    cb([{
                        "text": "Searching...",
                        "cleaned_text": text,
                        "selectable": false,
                    }]);
                }
            };
            xhr.open("GET", queryURL + "?q=" + text, true);
            xhr.send();
        }
        
        getValuesFunction(acURL) {
            var that = this;
            return function (text, cb) {
                that.remoteSearch(text, acURL, objects => cb(objects));
            };
        }
        
        getSelectTemplateFunction(trigger, regex = undefined) {
            return function (item) {
                var resultText = trigger + item.original.cleaned_text;
                
                if(typeof regex == undefined ||
                        !(regex instanceof RegExp))
                    return resultText;
                else {
                    var extract;
                    // check for global flag; otherwise the while loop will run forever (if there's a match)
                    if(!regex.global) {
                        if((extract = regex.exec(resultText)) !== null)
                            return extract[0];
                        else
                            return "";
                    } else {
                        var extractedText = "";
                        while((extract = regex.exec(resultText)) !== null) {
                            extractedText += extract[0];
                        } 
                        return extractedText;
                    }
                }
            };
        }
        
        addCollection(trigger, acURL, selectTemplateregex = undefined) {
            var collection = {};
            Object.assign(collection, this.defaultCollection);
            
            collection.trigger = trigger;
            collection.values = this.getValuesFunction(acURL);
            collection.selectTemplate = this.getSelectTemplateFunction(trigger, selectTemplateregex);
            
            this.collections.push(collection);
        }
        
        attach(element) {
            this.tributeObject = new tribute({collection: this.collections});
            this.tributeObject.attach(element);
        }
    }
})();