/* global oneApp, constants */
'use strict';

oneApp.directive('zemGridActionBar', [function () {
    return {
        restrict: 'E',
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            api: '=',
        },
        templateUrl: '/components/zem-grid-actions/templates/zem_grid_action_bar.html',
        controller: [function () {
            var vm = this;
            vm.isExportVisible = isExportVisible;

            function isExportVisible () {
                return vm.api.getMetaData().breakdown !== constants.breakdown.PUBLISHER;
            }
        }],
    };
}]);
