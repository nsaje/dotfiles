angular.module('one.widgets').component('zemInclusionTargetingList', {
    bindings: {
        texts: '<',
        targetings: '<',
        displaySections: '<?',
        addTargeting: '&',
        removeTargeting: '&',
        refreshTargetings: '&?',
    },
    templateUrl: '/app/widgets/zem-settings/common/inclusion-targeting-list/zemInclusionTargetingList.component.html',
    controller: function () {
        var $ctrl = this;
        var showTargetingEditSection;

        // template variables
        $ctrl.notSelected = [];

        // template functions
        $ctrl.enableTargetingEditSection = enableTargetingEditSection;
        $ctrl.isTargetingEditSectionVisible = isTargetingEditSectionVisible;
        $ctrl.groupBySection = groupBySection;
        $ctrl.addIncluded = addIncluded;
        $ctrl.addExcluded = addExcluded;
        $ctrl.onRefresh = onRefresh;
        $ctrl.remove = remove;

        $ctrl.$onInit = function () {
            setSelected();
        };

        $ctrl.$onChanges = function () {
            setSelected();
        };

        function enableTargetingEditSection () {
            showTargetingEditSection = true;
        }

        function isTargetingEditSectionVisible () {
            return showTargetingEditSection || $ctrl.included || $ctrl.excluded;
        }

        function groupBySection (targeting) {
            return targeting.section;
        }

        function addIncluded (targeting) {
            targeting.included = true;
            targeting.excluded = false;
            $ctrl.addTargeting({targeting: targeting});

            setSelected();
        }

        function addExcluded (targeting) {
            targeting.included = false;
            targeting.excluded = true;

            $ctrl.addTargeting({targeting: targeting});

            setSelected();
        }

        function remove (targeting) {
            targeting.included = false;
            targeting.excluded = false;

            $ctrl.removeTargeting({targeting: targeting});

            setSelected();
        }

        function setSelected () {
            var targeting, includedSections = {}, excludedSections = {}, notSelected = [];
            var includedCount = 0, excludedCount = 0;

            delete $ctrl.included;
            delete $ctrl.excluded;

            if (!$ctrl.targetings || !$ctrl.targetings.length) {
                return;
            }

            for (var i = 0; i < $ctrl.targetings.length; i++) {
                targeting = $ctrl.targetings[i];

                if (targeting.included) {
                    if (!includedSections[targeting.section]) {
                        includedSections[targeting.section] = [];
                    }
                    includedSections[targeting.section].push(targeting);
                    includedCount++;
                } else if (targeting.excluded) {
                    if (!excludedSections[targeting.section]) {
                        excludedSections[targeting.section] = [];
                    }
                    excludedSections[targeting.section].push(targeting);
                    excludedCount++;
                } else {
                    notSelected.push(targeting);
                }
            }

            $ctrl.notSelected = notSelected;
            if (includedCount > 0) {
                $ctrl.included = includedSections;
            }
            if (excludedCount > 0) {
                $ctrl.excluded = excludedSections;
            }
        }

        function onRefresh (searchTerm) {
            if (!$ctrl.refreshTargetings) {
                return;
            }
            $ctrl.refreshTargetings({searchTerm: searchTerm});
        }
    }
});
