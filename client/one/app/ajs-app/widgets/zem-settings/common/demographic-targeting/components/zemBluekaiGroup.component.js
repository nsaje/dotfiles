angular.module('one.widgets').component('zemBluekaiGroup', {
    bindings: {
        node: '<',
        stateService: '<',
    },
    template: require('./zemBluekaiGroup.component.html'),
    controller: function(
        zemUtils,
        zemDemographicTargetingConstants,
        zemDemographicTaxonomyService
    ) {
        var $ctrl = this;
        $ctrl.GROUP_TYPES = {
            DEFAULT: 0,
            NARROW: 1,
            EXCLUDE: 2,
        };

        zemDemographicTaxonomyService.getTaxonomy().then(function(data) {
            $ctrl.bluekaiTaxonomy = data;
        });

        $ctrl.getGroupType = getGroupType;
        $ctrl.removeGroup = removeGroup;
        $ctrl.onSelectionUpdate = onSelectionUpdate;

        $ctrl.$onInit = function() {
            $ctrl.mainGroup = $ctrl.node;
            if (
                $ctrl.node.type ===
                zemDemographicTargetingConstants.EXPRESSION_TYPE.NOT
            ) {
                $ctrl.mainGroup = $ctrl.node.childNodes[0];
            }

            $ctrl.initialCategories = $ctrl.mainGroup.childNodes.map(function(
                node
            ) {
                return node.value;
            });
        };

        function getGroupType() {
            if (
                $ctrl.node.type ===
                zemDemographicTargetingConstants.EXPRESSION_TYPE.NOT
            ) {
                return $ctrl.GROUP_TYPES.EXCLUDE;
            } else if (
                $ctrl.stateService.getState().expressionTree.childNodes[0] !==
                $ctrl.node
            ) {
                return $ctrl.GROUP_TYPES.NARROW;
            }
            return $ctrl.GROUP_TYPES.DEFAULT;
        }

        function onSelectionUpdate(categories) {
            $ctrl.stateService.updateCategories(
                $ctrl.mainGroup,
                categories,
                zemDemographicTargetingConstants.PROVIDER.BLUEKAI
            );
        }

        function removeGroup() {
            $ctrl.stateService.removeNode($ctrl.node);
        }
    },
});
