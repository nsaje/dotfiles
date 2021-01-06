require('./zemGrid.component.less');

angular.module('one.widgets').component('zemGrid', {
    bindings: {
        dataSource: '<',
        options: '<',
        renderingEngine: '<',
        page: '<',
        pageSize: '<',
        level: '<',
        breakdown: '<',
        onInitialized: '&',
        onPaginationChange: '&',
    },
    template: require('./zemGrid.component.html'),
    controller: function(
        $scope,
        $element,
        zemAuthStore,
        zemGridObject,
        zemGridPubSub,
        zemGridDataService,
        zemGridColumnsService,
        zemGridOrderService,
        zemGridSelectionService,
        zemGridCollapseService,
        zemGridConstants,
        zemGridApi
    ) {
        // eslint-disable-line max-len
        var $ctrl = this;
        var onMetaDataUpdatedHandler;

        $ctrl.gridRenderingEngineType =
            zemGridConstants.gridRenderingEngineType;

        this.$onChanges = function(changes) {
            if (!$ctrl.grid) return; // Not yet initialized
            $ctrl.grid.meta.renderingEngine = $ctrl.renderingEngine;
            if (!changes.dataSource && (changes.page || changes.pageSize)) {
                $ctrl.grid.meta.paginationOptions.page = $ctrl.page;
                $ctrl.grid.meta.paginationOptions.pageSize = $ctrl.pageSize;
                $ctrl.grid.meta.api.loadData();
            }
            if (changes.dataSource) {
                $ctrl.grid.meta.paginationOptions.page = $ctrl.page;
                $ctrl.grid.meta.paginationOptions.pageSize = $ctrl.pageSize;
                $ctrl.grid.meta.api.replaceDataSource($ctrl.dataSource);
            }
        };

        this.$onInit = function() {
            $ctrl.grid = new zemGridObject.createGrid();
            $ctrl.grid.ui.element = $element;
            $ctrl.grid.meta.paginationOptions.page = $ctrl.page;
            $ctrl.grid.meta.paginationOptions.pageSize = $ctrl.pageSize;
            $ctrl.grid.meta.renderingEngine = $ctrl.renderingEngine;
            $ctrl.grid.meta.scope = $scope;
            $ctrl.grid.meta.options = this.options || {};
            $ctrl.grid.meta.pubsub = zemGridPubSub.createInstance($scope);
            $ctrl.grid.meta.dataService = zemGridDataService.createInstance(
                this.grid,
                this.dataSource
            );

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
            $ctrl.grid.meta.api.hasPermission = zemAuthStore.hasPermission.bind(
                zemAuthStore
            );
            $ctrl.grid.meta.api.isPermissionInternal = zemAuthStore.isPermissionInternal.bind(
                zemAuthStore
            );

            // Initialize data service
            $ctrl.grid.meta.api.initialize();
            // Starts loading meta data
            $ctrl.grid.meta.api.loadMetaData();

            onMetaDataUpdatedHandler = $ctrl.grid.meta.api.onMetaDataUpdated(
                $ctrl.grid.meta.scope,
                handleMetaDataUpdate
            );
        };

        this.$onDestroy = function() {
            $ctrl.grid.meta.dataService.destroy();
            $ctrl.grid.meta.columnsService.destroy();
            $ctrl.grid.meta.orderService.destroy();
            $ctrl.grid.meta.collapseService.destroy();
            $ctrl.grid.meta.selectionService.destroy();
        };

        function handleMetaDataUpdate() {
            $ctrl.grid.meta.api.loadData();
            $ctrl.onInitialized({api: $ctrl.grid.meta.api});
            onMetaDataUpdatedHandler();
        }
    },
});
