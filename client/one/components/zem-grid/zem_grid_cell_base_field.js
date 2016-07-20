/* globals oneApp */
'use strict';

oneApp.directive('zemGridCellBaseField', [function () {

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            data: '=',
            column: '=',
            row: '=',
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_cell_base_field.html',
        controller: ['$scope', 'zemGridConstants', 'zemGridDataFormatter', 'zemGridUIService', function ($scope, zemGridConstants, zemGridDataFormatter, zemGridUIService) { // eslint-disable-line max-len
            var vm = this;

            $scope.$watch('ctrl.row', update);
            $scope.$watch('ctrl.data', update);

            function update () {
                vm.formattedValue = '';

                if (!isFieldVisible()) {
                    return;
                }

                var value = vm.data ? vm.data.value : undefined;
                vm.formattedValue = zemGridDataFormatter.formatValue(value, vm.column.data);

                vm.goalStatusClass = '';
                if (vm.data) {
                    vm.goalStatusClass = zemGridUIService.getFieldGoalStatusClass(vm.data.goalStatus);
                }
            }

            function isFieldVisible () {
                if (!vm.row || !vm.column) {
                    return false;
                }
                return !(vm.row.level === zemGridConstants.gridRowLevel.FOOTER && vm.column.data.totalRow === false);
            }
        }],
    };
}]);
