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
        controller: ['$scope', function ($scope) {
            var vm = this;

            // Set some dummy values to initialize zem-in-link
            vm.id = -1;
            vm.state = 'unknown';

            $scope.$watch('ctrl.row', update);
            $scope.$watch('ctrl.data', update);

            function update () {
                if (vm.data && vm.row.data && vm.row.level === 1) {
                    vm.id = vm.row.data.breakdownId || -1;
                    vm.state = getState(vm.grid.meta.data.level);
                }
            }

            function getState (level) {
                switch (level) {
                case constants.level.ALL_ACCOUNTS: return 'main.accounts.campaigns';
                case constants.level.ACCOUNTS: return 'main.campaigns.ad_groups';
                case constants.level.CAMPAIGNS: return 'main.adGroups.ads';
                default: return 'unknown';
                }
            }
        }],
    };
}]);
