/* globals oneApp */
'use strict';

oneApp.directive('zemGrid', ['config', 'zemGridConstants', 'zemGridService', function (config, zemGridConstants, zemGridService) { // eslint-disable-line max-len
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            dataSource: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid.html',
        controller: ['$scope', 'zemGridObject', 'zemGridPubSub', function ($scope, zemGridObject, zemGridPubSub) {

            var ctrl = this;
            var grid = new zemGridObject.createInstance();
            var pubsub = zemGridPubSub.createInstance($scope);

            grid.meta.pubsub = pubsub;
            grid.meta.source = this.dataSource;

            activate();

            function activate () {
                zemGridService.loadMetadata(grid).then(function () {
                    ctrl.grid = grid;
                    zemGridService.loadData(ctrl.grid);
                });
            }
        }],
    };
}]);
