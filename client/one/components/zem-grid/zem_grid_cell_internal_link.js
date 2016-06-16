/* globals oneApp */
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
            ctrl.id = -1;
            scope.$watch('ctrl.data', function () {
                if (ctrl.data && ctrl.row.data.breakdownId) {
                    ctrl.id = ctrl.row.data.breakdownId;
                    if (ctrl.grid.meta.data.level === 'all_accounts') {
                        ctrl.state = 'main.accounts.campaigns';
                    }
                    if (ctrl.grid.meta.data.level === 'accounts') {
                        ctrl.state = 'main.campaigns.ad_groups';
                    }
                    if (ctrl.grid.meta.data.level === 'campaigns') {
                        ctrl.state = 'main.adGroups.ads';
                    }
                    ctrl.zemInLinkReady = true;
                }
            });
        },
        controller: [function () {}],
    };
}]);
