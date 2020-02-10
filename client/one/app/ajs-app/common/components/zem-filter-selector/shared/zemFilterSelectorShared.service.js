angular
    .module('one.common')
    .service('zemFilterSelectorSharedService', function() {
        this.isSelectorExpanded = isSelectorExpanded;
        this.setSelectorExpanded = setSelectorExpanded;
        this.toggleSelector = toggleSelector;

        var selectorExpanded = false;

        //
        // Public methods
        //
        function isSelectorExpanded() {
            return selectorExpanded;
        }

        function setSelectorExpanded(expanded) {
            selectorExpanded = expanded;
            toggleBodyClass(selectorExpanded);
        }

        function toggleSelector() {
            selectorExpanded = !selectorExpanded;
            toggleBodyClass(selectorExpanded);
        }

        //
        // Private methods
        //
        function toggleBodyClass(selectorExpanded) {
            if (selectorExpanded) {
                $('body').addClass('filter-selector-expanded');
            } else {
                $('body').removeClass('filter-selector-expanded');
            }
        }
    });
