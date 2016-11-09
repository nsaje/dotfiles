angular.module('one.widgets').component('zemFilterSelector', {
    templateUrl: '/app/widgets/zem-filter-selector/zemFilterSelector.component.html',
    controller: function (zemDataFilterService, zemFilterSelectorService, zemFilterSelectorSharedService) { // eslint-disable-line max-len
        var $ctrl = this;

        $ctrl.isExpanded = zemFilterSelectorSharedService.isSelectorExpanded;
        $ctrl.removeCondition = zemFilterSelectorService.removeAppliedCondition;
        $ctrl.clearFilter = zemDataFilterService.resetAllConditions;
        $ctrl.applyFilter = applyFilter;
        $ctrl.getVisibleSectionsClasses = getVisibleSectionsClasses;

        $ctrl.$onInit = function () {
            zemFilterSelectorService.init();

            $ctrl.appliedConditions = [];
            $ctrl.visibleSections = [];

            zemFilterSelectorService.onSectionsUpdate(refresh);
            zemDataFilterService.onAppliedConditionsUpdate(refresh);
        };

        function applyFilter () {
            zemFilterSelectorService.applyFilter($ctrl.visibleSections);
            zemFilterSelectorSharedService.toggleSelector();
        }

        function getVisibleSectionsClasses () {
            var classes = '';
            $ctrl.visibleSections.forEach(function (section) {
                classes += 'filter-sections--visible-' + section.cssClass + ' ';
            });
            return classes;
        }

        function refresh () {
            $ctrl.appliedConditions = zemFilterSelectorService.getAppliedConditions();
            $ctrl.visibleSections = zemFilterSelectorService.getVisibleSections();

            // Add or remove data-filter-enabled class to body to enable global desing changes if data filter is enabled
            if ($ctrl.appliedConditions.length) {
                $('body').addClass('data-filter-enabled');
            } else {
                $('body').removeClass('data-filter-enabled');
            }
        }
    },
});
