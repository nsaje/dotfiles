/* globals angular, constants */
'use strict';

angular.module('one.legacy').directive('zemGridCellInternalLink', [function () {

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
        controller: ['$scope', 'zemGridConstants', function ($scope, zemGridConstants) {
            var vm = this;

            // Set some dummy values to initialize zem-in-link
            vm.id = -1;
            vm.state = 'unknown';

            $scope.$watch('ctrl.row', update);
            $scope.$watch('ctrl.data', update);

            function update () {
                vm.id = -1;
                vm.state = 'unknown';
                if (vm.data && vm.row.data && vm.row.entity) {
                    vm.id = vm.row.entity.id || -1;
                    vm.state = getState(vm.row.entity.type);
                }
            }

            function getState (entityType) {
                switch (entityType) {
                case constants.entityType.ACCOUNT: return 'main.accounts.campaigns';
                case constants.entityType.CAMPAIGN: return 'main.campaigns.ad_groups';
                case constants.entityType.AD_GROUP: return 'main.adGroups.ads';
                default: return 'unknown';
                }
            }
        }],
    };
}]);
