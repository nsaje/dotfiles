angular.module('one.widgets').component('zemInclusionTargetingList', {
    bindings: {
        texts: '<',
        targetings: '<',
        addTargeting: '&',
        removeTargeting: '&',
    },
    templateUrl: '/app/widgets/zem-settings/common/inclusion-targeting-list/zemInclusionTargetingList.component.html',
    controller: function () {
        var $ctrl = this;

        // template variables
        $ctrl.included = [];
        $ctrl.excluded = [];
        $ctrl.notSelected = [];
        $ctrl.currentlySelected = undefined;

        // template functions
        $ctrl.groupBySection = groupBySection;
        $ctrl.addIncluded = addIncluded;
        $ctrl.addExcluded = addExcluded;
        $ctrl.remove = remove;

        $ctrl.$onInit = function () {
            setSelected();
        };

        $ctrl.$onChanges = function () {
            setSelected();
        };

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
            var targeting, included = [], excluded = [], notSelected = [];

            if (!$ctrl.targetings || !$ctrl.targetings.length) {
                return;
            }

            for (var i = 0; i < $ctrl.targetings.length; i++) {
                targeting = $ctrl.targetings[i];

                if (targeting.included) {
                    included.push(targeting);
                } else if (targeting.excluded) {
                    excluded.push(targeting);
                } else {
                    notSelected.push(targeting);
                }
            }

            $ctrl.notSelected = notSelected;
            $ctrl.included = included;
            $ctrl.excluded = excluded;
        }

    }
});