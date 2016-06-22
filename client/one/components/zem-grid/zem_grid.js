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
            options: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid.html',
        controller: ['$scope', '$element', 'zemGridObject', 'zemGridPubSub', 'zemGridDataService', 'zemGridApi', function ($scope, $element, zemGridObject, zemGridPubSub, zemGridDataService, zemGridApi) { // eslint-disable-line max-len
            this.grid = new zemGridObject.createGrid();
            this.grid.ui.element = $element;
            this.grid.meta.scope = $scope;
            this.grid.meta.pubsub = zemGridPubSub.createInstance($scope);
            this.grid.meta.service = zemGridDataService.createInstance(this.grid, this.dataSource);
            this.grid.meta.options = this.options || {};

            // Define Grid API and assign to api variable to enable binding between zem-grid and controller
            this.grid.meta.api = zemGridApi.createInstance(this.grid);
            this.api = this.grid.meta.api;

            // Initialize data service; starts loading data
            this.grid.meta.service.initialize();
        }],
    };
}]);
