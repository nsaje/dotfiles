angular.module('one.widgets').component('zemHeaderFilterSelectorToggle', {
    templateUrl: '/app/widgets/zem-header/components/zem-header-filter-selector-toggle/zemHeaderFilterSelectorToggle.component.html', // eslint-disable-line max-len
    controller: ['config', 'zemFilterSelectorSharedService', function (config, zemFilterSelectorSharedService) {
        var $ctrl = this;
        $ctrl.config = config;
        $ctrl.toggleFilterSelector = zemFilterSelectorSharedService.toggleSelector;
    }],
});
