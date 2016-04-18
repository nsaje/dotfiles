/* globals oneApp, angular */
'use strict';

oneApp.directive('zemGridDebug', ['config', function (config) {

    return {
        restrict: 'E',
        require: ['zemGridDebug', '^zemGrid'], replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {},
        link: function (scope, element, attributes, ctrls) {
            ctrls[0].gridCtrl = ctrls[1];
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_debug.html',
        controller: ['zemGridUtil', function (zemGridUtil) {
            this.DEBUG_BREAKDOWNS = {'ad_group': true, 'age': true, 'sex': false, 'date': true};

            this.applyBreakdown = function () {
                var breakdowns = [];
                angular.forEach(this.DEBUG_BREAKDOWNS, function (value, key) {
                    if (value) breakdowns.push(key);
                });
                this.gridCtrl.dataSource.breakdowns = breakdowns;
                this.gridCtrl.dataSource.defaultPagination = [2, 3, 5, 7];
                this.gridCtrl.load();
            };

            this.toggleCollapseLevel = function (level) {
                zemGridUtil.toggleCollapseLevel(this.gridCtrl.grid, level);
            };
        }],
    };
}]);
