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
        controller: ['$scope', 'zemGridObject', 'zemGridPubSub', 'zemGridDataService', function ($scope, zemGridObject, zemGridPubSub, zemGridDataService) { // eslint-disable-line max-len
            var vm = this;

            this.grid = new zemGridObject.createInstance();
            this.grid.meta.scope = $scope;
            this.grid.meta.source = this.dataSource;
            this.grid.meta.pubsub = zemGridPubSub.createInstance($scope);
            this.grid.meta.service = zemGridDataService.createInstance(this.grid);

            this.grid.meta.service.initialize();
        }],
    };
}]);
