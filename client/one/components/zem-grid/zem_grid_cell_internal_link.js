/* globals oneApp, constants */
'use strict';

oneApp.directive('zemGridCellInternalLink', [function () {

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            data: '=',
            row: '=',
            column: '=',
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_cell_internal_link.html',
        link: function (scope, element, attributes, ctrl) {
            scope.$watch('ctrl.data', function () {
                if (ctrl.data && ctrl.row.data.breakdownId) {
                    ctrl.id = ctrl.row.data.breakdownId;
                    if (ctrl.grid.meta.data.level === constants.level.ALL_ACCOUNTS) {
                        ctrl.state = 'main.accounts.campaigns';
                    }
                    if (ctrl.grid.meta.data.level === constants.level.ACCOUNTS) {
                        ctrl.state = 'main.campaigns.ad_groups';
                    }
                    if (ctrl.grid.meta.data.level === constants.level.CAMPAIGNS) {
                        ctrl.state = 'main.adGroups.ads';
                    }
                    ctrl.zemInLinkReady = true;
                }
            });
        },
        controller: [function () {}],
    };
}]);
