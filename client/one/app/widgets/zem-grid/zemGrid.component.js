/* globals angular */
'use strict';

angular.module('one.widgets').component('zemGrid', {
    bindings: {
        dataSource: '=',
        api: '=',
        options: '=',
    },
    templateUrl: '/app/widgets/zem-grid/zemGrid.component.html',
    controller: function ($scope, $element, zemPermissions, zemGridObject, zemGridPubSub, zemGridDataService, zemGridColumnsService, zemGridOrderService, zemGridSelectionService, zemGridCollapseService, zemGridApi) { // eslint-disable-line max-len
        this.grid = new zemGridObject.createGrid();
        this.grid.ui.element = $element;
        this.grid.meta.scope = $scope;
        this.grid.meta.pubsub = zemGridPubSub.createInstance($scope);
        this.grid.meta.dataService = zemGridDataService.createInstance(this.grid, this.dataSource);
        this.grid.meta.options = this.options || {};

        // Extensions
        this.grid.meta.columnsService = zemGridColumnsService.createInstance(this.grid);
        this.grid.meta.orderService = zemGridOrderService.createInstance(this.grid);
        this.grid.meta.collapseService = zemGridCollapseService.createInstance(this.grid);
        this.grid.meta.selectionService = zemGridSelectionService.createInstance(this.grid);

        // Define Grid API and assign to api variable to enable binding between zem-grid and controller
        this.grid.meta.api = zemGridApi.createInstance(this.grid);
        this.grid.meta.api.hasPermission = zemPermissions.hasPermission;
        this.grid.meta.api.isPermissionInternal = zemPermissions.isPermissionInternal;
        this.api = this.grid.meta.api;

        // Initialize data service; starts loading data
        this.grid.meta.dataService.initialize();
    },
});
