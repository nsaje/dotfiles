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
        controller: ['$scope', 'zemGridDataFormatter', 'zemGridUIService', function ($scope, zemGridDataFormatter, zemGridUIService) { // eslint-disable-line max-len
            var vm = this;

            $scope.$watch('ctrl.row', update);
            $scope.$watch('ctrl.data', update);

            function update () {
                var value = vm.data ? vm.data.value : undefined;
                vm.parsedValue = zemGridDataFormatter.formatValue(value, vm.column.data);

                vm.goalStatusClass = '';
                if (vm.data) {
                    vm.goalStatusClass = zemGridUIService.getFieldGoalStatusClass(vm.data.goalStatus);
                }
            }
        }],
    };
}]);
