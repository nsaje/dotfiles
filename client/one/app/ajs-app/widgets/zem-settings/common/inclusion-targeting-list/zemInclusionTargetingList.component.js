angular.module('one.widgets').component('zemInclusionTargetingList', {
    bindings: {
        texts: '<',
        targetings: '<',
        displaySections: '<?',
        addIncluded: '&',
        addExcluded: '&',
        removeTargeting: '&',
        refreshTargetings: '&?',
    },
    template: require('./zemInclusionTargetingList.component.html'),
    controller: function() {
        var $ctrl = this;
        var showTargetingEditSection;

        $ctrl.include = include;
        $ctrl.exclude = exclude;
        $ctrl.remove = remove;

        // template functions
        $ctrl.enableTargetingEditSection = enableTargetingEditSection;
        $ctrl.isTargetingEditSectionVisible = isTargetingEditSectionVisible;
        $ctrl.groupBySection = groupBySection;
        $ctrl.onRefresh = onRefresh;

        function enableTargetingEditSection() {
            showTargetingEditSection = true;
        }

        function isTargetingEditSectionVisible() {
            if (!$ctrl.targetings) return;
            return (
                showTargetingEditSection ||
                $ctrl.targetings.included.length ||
                $ctrl.targetings.excluded.length
            );
        }

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
