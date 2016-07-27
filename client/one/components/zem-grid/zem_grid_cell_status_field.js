/* globals oneApp, constants */
'use strict';

oneApp.directive('zemGridCellStatusField', ['zemGridEndpointColumns', function (zemGridEndpointColumns) {

    function getStatusText (value, row, statusValuesAndTexts) {
        if (row.archived) {
            return 'Archived';
        }

        if (!statusValuesAndTexts || !statusValuesAndTexts.statusTexts) {
            return '';
        }

        return statusValuesAndTexts.statusTexts[value] || '';
    }

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            data: '=',
            row: '=',
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_cell_status_field.html',
        controller: ['$scope', 'zemGridStateAndStatusHelpers', function ($scope, zemGridStateAndStatusHelpers) {
            var vm = this;
            var pubsub = vm.grid.meta.pubsub;

            $scope.$watch('ctrl.row', update);
            $scope.$watch('ctrl.data', update);
            pubsub.register(pubsub.EVENTS.DATA_UPDATED, update);

            function update () {
                vm.statusText = '';

                if (vm.row && vm.data) {
                    var statusValuesAndTexts = zemGridStateAndStatusHelpers.getStatusValuesAndTexts(
                        vm.grid.meta.data.level,
                        vm.grid.meta.data.breakdown
                    );
                    vm.statusText = getStatusText(vm.data.value, vm.row, statusValuesAndTexts);
                }
            }
        }],
    };
}]);
