angular.module('one.widgets').component('zemGridContainer', {
    templateUrl: '/app/widgets/zem-grid-container/zemGridContainer.component.html',
    bindings: {
        entity: '<',
        breakdown: '<',
    },
    controller: function ($scope, zemGridIntegrationService) { // eslint-disable-line max-len
        var $ctrl = this;

        $ctrl.constants = constants;

        $ctrl.onGridInitialized = onGridInitialized;

        $ctrl.$onInit = function () {
            initializeGridIntegrationService();
            configureContainer();
        };

        $ctrl.$onChanges = function () {
            if (!$ctrl.gridIntegrationService) return;
            configureContainer();
        };

        function initializeGridIntegrationService () {
            $ctrl.gridIntegrationService = zemGridIntegrationService.createInstance($scope);
            $ctrl.gridIntegrationService.initialize();
            $ctrl.grid = $ctrl.gridIntegrationService.getGrid();
        }

        function configureContainer () {
            $ctrl.level = $ctrl.entity ?
                $ctrl.constants.entityTypeToLevelMap[$ctrl.entity.type] :
                $ctrl.constants.level.ALL_ACCOUNTS;

            if ($ctrl.breakdown !== constants.breakdown.INSIGHTS) {
                $ctrl.gridIntegrationService.configureDataSource($ctrl.entity, $ctrl.breakdown);
            }
        }

        function onGridInitialized (gridApi) {
            $ctrl.gridIntegrationService.setGridApi(gridApi);
        }
    },
});
