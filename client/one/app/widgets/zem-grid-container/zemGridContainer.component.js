angular.module('one.widgets').component('zemGridContainer', {
    templateUrl: '/app/widgets/zem-grid-container/zemGridContainer.component.html',
    bindings: {
        entity: '<',
        breakdown: '<',
    },
    controller: function ($scope, $timeout, zemGridEndpointService, zemDataSourceService, zemGridIntegrationService) {
        var $ctrl = this;
        $ctrl.breakdown = constants.breakdown.CAMPAIGN;

        $ctrl.onTabSelected = onTabSelected;
        $ctrl.onGridInitialized = onGridInitialized;

        $ctrl.$onInit = function () {
            $ctrl.gridIntegrationService = zemGridIntegrationService.createInstance($ctrl.entity, $scope);
            $ctrl.gridIntegrationService.initialize();
            $ctrl.gridIntegrationService.setBreakdown($ctrl.breakdown);
            $ctrl.grid = $ctrl.gridIntegrationService.getGrid();

            $ctrl.tabOptions = createTabOptions();
        };

        $ctrl.$onChanges = function () {
            if (!$ctrl.gridIntegrationService) return;
            $ctrl.gridIntegrationService.setBreakdown($ctrl.breakdown);
        };

        function onGridInitialized (gridApi) {
            $ctrl.gridIntegrationService.setGridApi(gridApi);
        }

        function createTabOptions () {
            // TODO - based on entity type
            return [
                {name: 'Campaigns', breakdown: constants.breakdown.CAMPAIGN},
                {name: 'Sources', breakdown: constants.breakdown.MEDIA_SOURCE},
                {name: 'Content Insights', breakdown: 'insights'},
            ];
        }

        function onTabSelected (option) {
            // TODO: This will be communicated through router
            $ctrl.breakdown = option.breakdown;
            $ctrl.gridIntegrationService.setBreakdown($ctrl.breakdown);
        }
    },
});
