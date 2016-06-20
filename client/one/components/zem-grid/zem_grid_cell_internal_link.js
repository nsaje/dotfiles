/* globals oneApp, constants */
'use strict';

oneApp.directive('zemGridCellInternalLink', [function () {

    function updateRow (ctrl) {
        if (ctrl.data && ctrl.row.data.breakdownId) {
            ctrl.id = ctrl.row.data.breakdownId;
            ctrl.state = getState(ctrl.grid.meta.data.level);
        }
    }

    function getState (level) {
        switch (level) {
        case constants.level.ALL_ACCOUNTS: return 'main.accounts.campaigns';
        case constants.level.ACCOUNTS: return 'main.campaigns.ad_groups';
        case constants.level.CAMPAIGNS: return 'main.adGroups.ads';
        }
    }

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
        link: {
            pre: function (scope, element, attributes, ctrl) {
                // Set some dummy values to initialize zem-in-link
                ctrl.id = -1;
                ctrl.state = 'unknown';
            },
            post: function (scope, element, attributes, ctrl) {
                scope.$watch('ctrl.row', function () {
                    updateRow(ctrl);
                });
            },
        },
        controller: [function () {}],
    };
}]);
