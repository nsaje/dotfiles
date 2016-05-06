/* globals oneApp, angular */
'use strict';

oneApp.directive('zemGridDebug', [function () {

    return {
        restrict: 'E',
        require: ['zemGridDebug'], replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_debug.html',
        controller: ['zemGridService', function (zemGridService) {
            this.DEBUG_BREAKDOWNS = {'ad_group': true, 'age': true, 'sex': false, 'date': true};

            this.applyBreakdown = function () {
                var breakdowns = [];
                angular.forEach(this.DEBUG_BREAKDOWNS, function (value, key) {
                    if (value) breakdowns.push(key);
                });
                this.grid.meta.source.breakdowns = breakdowns;
                this.grid.meta.source.defaultPagination = [2, 3, 5, 7];
                zemGridService.load(this.grid.meta.source).then(function (grid) {
                    this.grid = grid;
                }.bind(this));
            };

            this.toggleCollapseLevel = function (level) {
                zemGridService.toggleCollapseLevel(this.gridCtrl.grid, level);
            };
        }],
    };
}]);
