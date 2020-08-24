require('./zemDemographicTargeting.component.less');

angular.module('one.common').component('zemDemographicTargeting', {
    bindings: {
        bluekaiTargeting: '<',
        entityId: '<', // Workaround to know when to reinitialize state service (on entity change)
        isDisabled: '<',
        onUpdate: '&',
    },
    template: require('./zemDemographicTargeting.component.html'),
    controller: function(
        zemDemographicTaxonomyService,
        zemDemographicTargetingConstants,
        zemDemographicTargetingStateService
    ) {
        var $ctrl = this;

        $ctrl.isEnabled = isEnabled;
        $ctrl.addInclusion = addInclusion;
        $ctrl.addExclusion = addExclusion;
        $ctrl.canAddExclusion = canAddExclusion;
        $ctrl.canAddInclusion = canAddInclusion;

        $ctrl.$onInit = function() {
            $ctrl.stateService = zemDemographicTargetingStateService.createInstance(
                onUpdate
            );
        };

        $ctrl.$onChanges = function(changes) {
            if (changes.entityId) {
                zemDemographicTaxonomyService.getTaxonomy().then(initialize);
            }
        };

        function initialize() {
            $ctrl.stateService.initialize($ctrl.bluekaiTargeting);
            $ctrl.state = $ctrl.stateService.getState();
            if (
                $ctrl.bluekaiTargeting &&
                Object.keys($ctrl.bluekaiTargeting).length === 0
            ) {
                // Workaround to initialize bluekai targeting state
                var root = $ctrl.stateService.createNode(
                    zemDemographicTargetingConstants.EXPRESSION_TYPE.AND,
                    null,
                    true
                );
                $ctrl.stateService.createNode(
                    zemDemographicTargetingConstants.EXPRESSION_TYPE.OR,
                    root,
                    true
                );
            }
        }

        function isEnabled() {
            if ($ctrl.state && $ctrl.state.expressionTree) {
                return $ctrl.state.expressionTree.childNodes.length > 0;
            }
            return false;
        }

        function onUpdate(bluekaiTargeting) {
            $ctrl.onUpdate({$event: bluekaiTargeting});
        }

        function addExclusion() {
            var notNode = $ctrl.stateService.createNode(
                zemDemographicTargetingConstants.EXPRESSION_TYPE.NOT,
                $ctrl.state.expressionTree
            );
            $ctrl.stateService.createNode(
                zemDemographicTargetingConstants.EXPRESSION_TYPE.OR,
                notNode
            );
        }

        function addInclusion() {
            $ctrl.stateService.createNode(
                zemDemographicTargetingConstants.EXPRESSION_TYPE.OR,
                $ctrl.state.expressionTree
            );
        }

        function canAddExclusion() {
            var tree = $ctrl.state.expressionTree;
            if (!tree) return false;

            return (
                tree.childNodes.filter(function(node) {
                    return (
                        node.type ===
                        zemDemographicTargetingConstants.EXPRESSION_TYPE.NOT
                    );
                }).length < 1
            );
        }

        function canAddInclusion() {
            var tree = $ctrl.state.expressionTree;
            if (!tree) return false;

            return (
                tree.childNodes.filter(function(node) {
                    return (
                        node.type ===
                        zemDemographicTargetingConstants.EXPRESSION_TYPE.OR
                    );
                }).length < 2
            );
        }
    },
});
