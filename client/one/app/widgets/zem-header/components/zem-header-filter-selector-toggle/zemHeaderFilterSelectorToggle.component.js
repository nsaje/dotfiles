angular.module('one.widgets').component('zemHeaderFilterSelectorToggle', {
    templateUrl: '/app/widgets/zem-header/components/zem-header-filter-selector-toggle/zemHeaderFilterSelectorToggle.component.html', // eslint-disable-line max-len
    controller: function (zemFilterSelectorSharedService) {
        var $ctrl = this;
        $ctrl.toggleFilterSelector = zemFilterSelectorSharedService.toggleSelector;
    },
});
