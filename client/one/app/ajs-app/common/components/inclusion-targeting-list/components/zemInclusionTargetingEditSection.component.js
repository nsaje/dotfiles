angular.module('one.common').component('zemInclusionTargetingEditSection', {
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
    template: require('./zemInclusionTargetingEditSection.component.html'), // eslint-disable-line max-len
    controller: function() {
        var $ctrl = this;
        var SECTION_LIMIT = 5;
        $ctrl.expandedSections = [];
        $ctrl.expandSection = expandSection;
        $ctrl.getSectionLimit = getSectionLimit;
        $ctrl.onItemSelected = onItemSelected;

        $ctrl.$onChanges = function(changes) {
            if (!changes.selectedItems) return;

            var sectionOrder = [];
            var selectedItemsBySection = {};
            ($ctrl.selectedItems || []).forEach(function(targeting) {
                if (sectionOrder.indexOf(targeting.section) === -1) {
                    sectionOrder.push(targeting.section);
                }
                if (!selectedItemsBySection[targeting.section]) {
                    selectedItemsBySection[targeting.section] = [];
                }
                selectedItemsBySection[targeting.section].push(targeting);
            });
            $ctrl.sectionOrder = sectionOrder;
            $ctrl.selectedItemsBySection = selectedItemsBySection;
        };

        function expandSection(section) {
            $ctrl.expandedSections.push(section);
        }

        function getSectionLimit(section) {
            if ($ctrl.expandedSections.indexOf(section) === -1) {
                return SECTION_LIMIT;
            }
        }

        function onItemSelected(item) {
            expandSection(item.section);
            $ctrl.onSelect(item);
        }
    },
});
