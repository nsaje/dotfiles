angular.module('one.widgets').service('zemFilterSelectorSharedService', function () {
    this.isSelectorExpanded = isSelectorExpanded;
    this.setSelectorExpanded = setSelectorExpanded;
    this.toggleSelector = toggleSelector;

    var selectorExpanded = false;

    //
    // Public methods
    //
    function isSelectorExpanded () {
        return selectorExpanded;
    }

    function setSelectorExpanded (expanded) {
        selectorExpanded = expanded;
    }

    function toggleSelector () {
        selectorExpanded = !selectorExpanded;
    }
});
