angular.module('one.widgets').directive('zemGridCellCloneButton', function() {
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
        template: require('./zemGridCellCloneButton.component.html'),
        controller: function($scope, zemGridConstants, zemCloneAdGroupService) {
            // eslint-disable-line max-len
            var vm = this;
            vm.cloneRow = cloneRow;
            vm.isFieldVisible = false;

            $scope.$watch('ctrl.row', update);

            function update() {
                if (vm.row) {
                    vm.isFieldVisible = isFieldVisible(vm.row.level);
                }
            }

            function cloneRow() {
                zemCloneAdGroupService
                    .openCloneModal(vm.grid.meta.data.id, vm.row.entity.id)
                    .then(function() {
                        vm.grid.meta.api.loadData();
                    });
            }

            function isFieldVisible(rowLevel) {
                return rowLevel === zemGridConstants.gridRowLevel.BASE;
            }
        },
    };
});
