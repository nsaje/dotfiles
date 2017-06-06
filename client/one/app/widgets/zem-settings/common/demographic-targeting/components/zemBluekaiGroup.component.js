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

        $ctrl.getHeaderText = getHeaderText;
        $ctrl.removeGroup = removeGroup;
        $ctrl.onSelectionUpdate = onSelectionUpdate;

        $ctrl.$onInit = function () {
            $ctrl.mainGroup = $ctrl.node;
            if ($ctrl.node.type === zemDemographicTargetingConstants.EXPRESSION_TYPE.NOT) {
                $ctrl.mainGroup = $ctrl.node.childNodes[0];
            }

            $ctrl.initialCategories = $ctrl.mainGroup.childNodes.map(function (node) {
                return node.value;
            });
        };

        function getHeaderText () {
            var prefix = 'INCLUDE';
            if ($ctrl.node.type === zemDemographicTargetingConstants.EXPRESSION_TYPE.NOT) {
                prefix = 'EXCLUDE';
            } else if ($ctrl.stateService.getState().expressionTree.childNodes[0] !== $ctrl.node) {
                prefix = 'AND INCLUDE';
            }

            return prefix + ' target users belonging to any of the following segments:';
        }

        function onSelectionUpdate (categories) {
            $ctrl.stateService.updateCategories($ctrl.mainGroup, categories,
                zemDemographicTargetingConstants.PROVIDER.BLUEKAI);
        }

        function removeGroup () {
            $ctrl.stateService.removeNode($ctrl.node);
        }
    },
});
