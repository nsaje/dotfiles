/* globals oneApp */
'use strict';

oneApp.directive('zemGrid', [function () {
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            dataSource: '=',
            api: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid.html',
        controller: ['$scope', 'zemGridObject', 'zemGridPubSub', 'zemGridDataService', 'zemGridApi', function ($scope, zemGridObject, zemGridPubSub, zemGridDataService, zemGridApi) { // eslint-disable-line max-len
            this.grid = new zemGridObject.createInstance();
            this.grid.meta.scope = $scope;
            this.grid.meta.pubsub = zemGridPubSub.createInstance($scope);
            this.grid.meta.service = zemGridDataService.createInstance(this.grid, this.dataSource);

            // Define Grid API and assign to api variable to enable binding between zem-grid and controller
            this.grid.meta.api = zemGridApi.createInstance(this.grid);
            this.api = this.grid.meta.api;

            // Initialize data service; starts loading data
            this.grid.meta.service.initialize();
        }],
    };
}]);
