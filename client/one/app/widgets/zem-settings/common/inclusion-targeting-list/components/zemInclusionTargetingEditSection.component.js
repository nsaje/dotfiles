angular.module('one.widgets').component('zemInclusionTargetingEditSection', {
    bindings: {
        selectedTitleClass: '@',
        selectedTitle: '@',
        selectedItems: '<',
        unselectedItems: '<',
        displaySections: '<',
        disabled: '<',
        remove: '<',
        groupBy: '<',
        onSelect: '<',
        onRefresh: '<',
        selectTargetingButtonText: '@',
        noChoiceText: '@',
    },
    templateUrl: '/app/widgets/zem-settings/common/inclusion-targeting-list/components/zemInclusionTargetingEditSection.component.html', // eslint-disable-line max-len
    controller: function () {
        var $ctrl = this;
        var SECTION_LIMIT = 5;
        $ctrl.expandedSections = [];
        $ctrl.expandSection = expandSection;
        $ctrl.getSectionLimit = getSectionLimit;
        $ctrl.onItemSelected = onItemSelected;

        function expandSection (section) {
            $ctrl.expandedSections.push(section);
        }

        function getSectionLimit (section) {
            if ($ctrl.expandedSections.indexOf(section) === -1) {
                return SECTION_LIMIT;
            }
        }

        function onItemSelected (item) {
            expandSection(item.section);
            $ctrl.onSelect(item);
        }
    }
});
