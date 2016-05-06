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
        controller: ['$scope', 'zemGridPubSub', function ($scope, zemGridPubSub) {

            var ctrl = this;
            ctrl.grid = null;
            ctrl.pubsub = zemGridPubSub.createInstance($scope);

            activate();

            function activate () {
                zemGridService.load(ctrl.dataSource).then(function (grid) {
                    ctrl.grid = grid;
                });
            }
        }],
    };
}]);
