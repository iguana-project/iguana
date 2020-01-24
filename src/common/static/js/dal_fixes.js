(function () {
    // focus the cursor after removing an element via Backspace
    $(document).on("select2:unselecting", ".select2-hidden-accessible", function() {
        var searchField = $(this).parent().find(".select2-search__field");
        
        setTimeout(function(){
            searchField.focus();
        }, 100);
    });
    
    // set proper text when removing an element (avoid html code)
    $(document).on("select2:unselect", ".select2-hidden-accessible", function(evt) {
        evt.params.data.text = evt.params.data.cleaned_text;
    });
    
    // after inserting an element, open the autocomplete view again
    $(document).on("select2:select", ".select2-hidden-accessible", function() {
        var self = $(this);
        
        setTimeout(function(){
            self.select2("open");
        }, 100);
    });
})();