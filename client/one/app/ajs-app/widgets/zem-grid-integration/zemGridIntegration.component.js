require('./zemGridIntegration.component.less');

angular.module('one.widgets').component('zemGridIntegration', {
    bindings: {
        api: '=api',
        options: '=options',

        level: '=level',
        breakdown: '=breakdown',
        entityId: '=entityId',
    },
    template: require('./zemGridIntegration.component.html'),
    controller: function($scope, zemGridIntegrationService) {
        // eslint-disable-line max-len
        var $ctrl = this;
        $ctrl.grid = undefined;

        $ctrl.$onInit = function() {
            var entity = $ctrl.entityId
                ? {
                      type: constants.levelToEntityTypeMap[$ctrl.level],
                      id: $ctrl.entityId,
                  }
                : null;
            $ctrl.gridIntegrationService = zemGridIntegrationService.createInstance(
                $scope
            );
            $ctrl.gridIntegrationService.initialize();
            $ctrl.gridIntegrationService.configureDataSource(
                entity,
                $ctrl.breakdown
            );
            $ctrl.grid = $ctrl.gridIntegrationService.getGrid();
        };

        $ctrl.onGridInitialized = function(gridApi) {
            $ctrl.api = gridApi;
            $ctrl.gridIntegrationService.setGridApi(gridApi);
        };
    },
});
