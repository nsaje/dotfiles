/* globals angular, constants */

angular.module('one.widgets').component('zemGridIntegration', {
    bindings: {
        api: '=api',
        options: '=options',

        level: '=level',
        breakdown: '=breakdown',
        entityId: '=entityId',
    },
    templateUrl: '/app/widgets/zem-grid-integration/zemGridIntegration.component.html',
    controller: function ($scope, zemGridIntegrationService) { // eslint-disable-line max-len
        var $ctrl = this;
        $ctrl.grid = undefined;

        $ctrl.$onInit = function () {
            var entity = {level: $ctrl.level, id: $ctrl.entityId};
            $ctrl.gridIntegrationService = zemGridIntegrationService.createInstance(entity, $scope);
            $ctrl.gridIntegrationService.initialize();
            $ctrl.gridIntegrationService.setBreakdown($ctrl.breakdown);
            $ctrl.grid = $ctrl.gridIntegrationService.getGrid();
        };

        $ctrl.onGridInitialized = function (gridApi) {
            $ctrl.api = gridApi;
            $ctrl.gridIntegrationService.setGridApi(gridApi);
        };
    }
});

