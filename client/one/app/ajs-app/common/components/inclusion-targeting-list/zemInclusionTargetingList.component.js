require('./zemInclusionTargetingList.component.less');

angular.module('one.common').component('zemInclusionTargetingList', {
    bindings: {
        texts: '<',
        targetings: '<',
        displaySections: '<?',
        isDisabled: '<',
        addIncluded: '&',
        addExcluded: '&',
        removeTargeting: '&',
        refreshTargetings: '&?',
    },
    template: require('./zemInclusionTargetingList.component.html'),
    controller: function() {
        var $ctrl = this;

        $ctrl.include = include;
        $ctrl.exclude = exclude;
        $ctrl.remove = remove;

        // template functions
        $ctrl.groupBySection = groupBySection;
        $ctrl.onRefresh = onRefresh;

        function groupBySection(targeting) {
            return $ctrl.displaySections && targeting.section;
        }

        function include(targeting) {
            $ctrl.addIncluded({targeting: targeting});
        }

        function exclude(targeting) {
            $ctrl.addExcluded({targeting: targeting});
        }

        function remove(targeting) {
            $ctrl.removeTargeting({targeting: targeting});
        }

        function onRefresh(searchTerm) {
            if (!$ctrl.refreshTargetings) {
                return;
            }
            $ctrl.refreshTargetings({searchTerm: searchTerm});
        }
    },
});
