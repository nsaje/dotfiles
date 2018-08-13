angular.module('one.widgets').component('zemHeaderFilterSelectorToggle', {
    template: require('./zemHeaderFilterSelectorToggle.component.html'), // eslint-disable-line max-len
    controller: function(zemFilterSelectorSharedService) {
        var $ctrl = this;
        $ctrl.toggleFilterSelector =
            zemFilterSelectorSharedService.toggleSelector;
        $ctrl.isSelectorExpanded =
            zemFilterSelectorSharedService.isSelectorExpanded;
    },
});
