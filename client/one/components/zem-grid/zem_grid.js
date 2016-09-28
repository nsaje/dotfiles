/* globals angular */
'use strict';

angular.module('one.legacy').directive('zemGrid', [function () {
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            dataSource: '=',
            api: '=',
            options: '=',
            hasPermission: '=zemHasPermission',
            isPermissionInternal: '=zemIsPermissionInternal',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid.html',
        controller: ['$scope', '$element', 'zemGridObject', 'zemGridPubSub', 'zemGridDataService', 'zemGridColumnsService', 'zemGridOrderService', 'zemGridSelectionService', 'zemGridCollapseService', 'zemGridApi', 'zemGridBulkActionsService', function ($scope, $element, zemGridObject, zemGridPubSub, zemGridDataService, zemGridColumnsService, zemGridOrderService, zemGridSelectionService, zemGridCollapseService, zemGridApi, zemGridBulkActionsService) { // eslint-disable-line max-len
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
            this.grid.meta.bulkActionsService = zemGridBulkActionsService.createInstance(this.grid);

            // Define Grid API and assign to api variable to enable binding between zem-grid and controller
            this.grid.meta.api = zemGridApi.createInstance(this.grid);
            this.grid.meta.api.hasPermission = this.hasPermission;
            this.grid.meta.api.isPermissionInternal = this.isPermissionInternal;
            this.api = this.grid.meta.api;

            // Initialize data service; starts loading data
            this.grid.meta.dataService.initialize();
        }],
    };
}]);
