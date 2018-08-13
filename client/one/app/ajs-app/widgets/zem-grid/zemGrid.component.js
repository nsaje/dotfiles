require('./zemGrid.component.less');

angular.module('one.widgets').component('zemGrid', {
    bindings: {
        dataSource: '<',
        options: '<',
        onInitialized: '&',
    },
    template: require('./zemGrid.component.html'),
    controller: function(
        $scope,
        $element,
        zemPermissions,
        zemGridObject,
        zemGridPubSub,
        zemGridDataService,
        zemGridColumnsService,
        zemGridOrderService,
        zemGridSelectionService,
        zemGridCollapseService,
        zemGridApi
    ) {
        // eslint-disable-line max-len
        var $ctrl = this;

        this.$onChanges = function() {
            if (!$ctrl.grid) return; // Not yet initialized

            // TODO: check data source
            $ctrl.grid.meta.dataService.replaceDataSource($ctrl.dataSource);
        };

        this.$onInit = function() {
            $ctrl.grid = new zemGridObject.createGrid();
            $ctrl.grid.ui.element = $element;
            $ctrl.grid.meta.scope = $scope;
            $ctrl.grid.meta.pubsub = zemGridPubSub.createInstance($scope);
            $ctrl.grid.meta.dataService = zemGridDataService.createInstance(
                this.grid,
                this.dataSource
            );
            $ctrl.grid.meta.options = this.options || {};

            // Extensions
            $ctrl.grid.meta.columnsService = zemGridColumnsService.createInstance(
                this.grid
            );
            $ctrl.grid.meta.orderService = zemGridOrderService.createInstance(
                this.grid
            );
            $ctrl.grid.meta.collapseService = zemGridCollapseService.createInstance(
                this.grid
            );
            $ctrl.grid.meta.selectionService = zemGridSelectionService.createInstance(
                this.grid
            );

            // Define Grid API and assign to api variable to enable binding between zem-grid and controller
            $ctrl.grid.meta.api = zemGridApi.createInstance(this.grid);
            $ctrl.grid.meta.api.hasPermission = zemPermissions.hasPermission;
            $ctrl.grid.meta.api.isPermissionInternal =
                zemPermissions.isPermissionInternal;

            // Initialize data service; starts loading data
            $ctrl.grid.meta.dataService.initialize();
            $ctrl.onInitialized({api: $ctrl.grid.meta.api});
        };
    },
});
