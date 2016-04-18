/* globals oneApp, angular */
'use strict';

oneApp.directive('zemGrid', ['config', 'zemGridConstants', 'zemGridUtil', 'zemDataSourceService', function (config, zemGridConstants, zemGridUtil, zemDataSourceService) {
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {},
        templateUrl: '/components/zem-grid/templates/zem_grid.html',
        controller: ['$scope', function ($scope) {
            var ctrl = this;

            ctrl.dataSource = new zemDataSourceService();

            ctrl.broadcastEvent = broadcastEvent;

            activate();

            function activate () {
                zemGridUtil.load(ctrl.dataSource).then(function (grid) {
                    ctrl.grid = grid;
                });
            }

            function broadcastEvent (event, data) {
                $scope.$broadcast(event, data);
            }
        }],
    };
}]);
