angular.module('one.widgets').component('zemBluekaiGroup', {
    bindings: {
        node: '<',
        stateService: '<',
    },
    templateUrl: '/app/widgets/zem-settings/common/demographic-targeting/components/zemBluekaiGroup.component.html',
    controller: function (zemUtils, zemDemographicTargetingConstants, zemDemographicTaxonomyService) {
        var $ctrl = this;
        zemDemographicTaxonomyService.getTaxonomy().then(function (data) {
            $ctrl.bluekaiTaxonomy = data;
        });

        $ctrl.removeGroup = removeGroup;
        $ctrl.onSelectionUpdate = onSelectionUpdate;

        $ctrl.$onInit = function () {

            var excludeGroup = false;
            $ctrl.mainGroup = $ctrl.node;
            if ($ctrl.node.type === zemDemographicTargetingConstants.EXPRESSION_TYPE.NOT) {
                excludeGroup = true;
                $ctrl.mainGroup = $ctrl.node.childNodes[0];
            }

            $ctrl.initialCategories = $ctrl.mainGroup.childNodes.map(function (node) {
                return node.value;
            });


            if ($ctrl.stateService.getState().expressionTree.childNodes[0] === $ctrl.node) {
                $ctrl.header = excludeGroup ? 'DON\'T target users belonging to any of the following segments:'
                                            : 'Target users belonging to any of the following segments:';
            } else {
                $ctrl.header = excludeGroup ? 'AND DON\'T target users belonging to any of the following segments:'
                                            : 'AND target users belonging to any of the following segments:';
            }
        };

        function onSelectionUpdate (categories) {
            $ctrl.stateService.updateCategories($ctrl.mainGroup, categories,
                zemDemographicTargetingConstants.PROVIDER.BLUEKAI);
        }

        function removeGroup () {
            $ctrl.stateService.removeNode($ctrl.node);
        }
    },
});
