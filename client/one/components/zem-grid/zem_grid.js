/* globals oneApp, angular */
'use strict';

oneApp.directive('zemGrid', [function () {
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            dataSource: '=',
            gridApi: '=', // onSelectionChanged, ... interaction service
        },
        templateUrl: '/components/zem-grid/templates/zem_grid.html',
        controller: ['$scope', 'zemGridObject', 'zemGridPubSub', 'zemGridDataService', function ($scope, zemGridObject, zemGridPubSub, zemGridDataService) { // eslint-disable-line max-len

            this.grid = new zemGridObject.createInstance();
            this.grid.meta.scope = $scope;
            this.grid.meta.api = this.gridApi;
            this.grid.meta.pubsub = zemGridPubSub.createInstance($scope);
            this.grid.meta.service = zemGridDataService.createInstance(this.grid, this.dataSource);

            initialize(this.grid);

            function initialize (grid) {
                initializeApi(grid);
                grid.meta.service.initialize();
            }

            function initializeApi (grid) {
                // Initialize API with mocked functions if not provided
                grid.meta.api = grid.meta.api || {};
                grid.meta.api.onSelectionChanged = grid.meta.api.onSelectionChanged || angular.noop;
            }
        }],
    };
}]);
