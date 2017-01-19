/* globals angular */
'use strict';

angular.module('one.widgets').directive('zemGridCellBaseField', function () {

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
        templateUrl: '/app/widgets/zem-grid/components/cell/zemGridCellBaseField.component.html',
        controller: function ($scope, zemGridConstants, zemGridDataFormatter, zemGridUIService) { // eslint-disable-line max-len
            var vm = this;

            $scope.$watch('ctrl.row', update);
            $scope.$watch('ctrl.data', update);

            function update () {
                vm.formattedValue = '';

                if (!isFieldVisible()) {
                    return;
                }

                var value = vm.data ? vm.data.value : undefined;
                vm.formattedValue = '';
                if (vm.row.type === zemGridConstants.gridRowType.STATS) {
                    vm.formattedValue = zemGridDataFormatter.formatValue(value, vm.column.data);
                }

                vm.class = vm.column.type + '-field';
                if (vm.data) {
                    vm.class += ' ' + zemGridUIService.getFieldGoalStatusClass(vm.data.goalStatus);
                }
            }

            function isFieldVisible () {
                if (!vm.row || !vm.column) {
                    return false;
                }
                return !(vm.row.level === zemGridConstants.gridRowLevel.FOOTER && vm.column.data.totalRow === false);
            }
        },
    };
});
