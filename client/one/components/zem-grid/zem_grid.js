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

            init();

            function init () {
                zemGridService.loadMetadata(grid).then(function () {
                    // After meta data is loaded in Grid, bind it to controller
                    // so that it is passed to child directives through defined bindings
                    ctrl.grid = grid;
                    zemGridService.loadData(ctrl.grid);
                });
            }
        }],
    };
}]);
