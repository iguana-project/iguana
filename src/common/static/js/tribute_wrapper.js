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
            lookup: "selected_text",
            fillAttr: "selected_text",
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
                        "selected_text": text,
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
        
        getSelectTemplateFunction(trigger) {
            return function (item) {
                // the selected text should not contain any spaces
                return trigger + item.original.selected_text.split(/\s/, 1)[0];
            };
        }
        
        addCollection(trigger, acURL) {
            var collection = {};
            Object.assign(collection, this.defaultCollection);
            
            collection.trigger = trigger;
            collection.values = this.getValuesFunction(acURL);
            collection.selectTemplate = this.getSelectTemplateFunction(trigger);
            
            this.collections.push(collection);
        }
        
        attach(element) {
            this.tributeObject = new tribute({collection: this.collections});
            this.tributeObject.attach(element);
        }
    }
})();