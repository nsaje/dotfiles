angular.module('one.widgets').directive('zemGridCellCheckbox', function() {
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            col: '=',
            row: '=',
            grid: '=',
        },
        template: require('./zemGridCellCheckbox.component.html'),
        controller: function($scope) {
            var vm = this;
            var selectionService = this.grid.meta.selectionService;

            vm.checkboxModel = {};
            vm.toggleSelection = toggleSelection;

            initialize();

            function initialize() {
                var pubsub = vm.grid.meta.pubsub;
                updateModel();
                pubsub.register(
                    pubsub.EVENTS.EXT_SELECTION_UPDATED,
                    $scope,
                    updateModel
                );
                $scope.$watch('ctrl.row', updateModel);
            }

            function updateModel() {
                if (!vm.row) return;
                vm.checkboxModel.visible = selectionService.isRowSelectionEnabled(
                    vm.row
                );
                if (vm.checkboxModel.visible) {
                    vm.checkboxModel.checked = selectionService.isRowSelected(
                        vm.row
                    );
                    vm.checkboxModel.disabled = !selectionService.isRowSelectable(
                        vm.row
                    );
                    vm.checkboxModel.tooltip = selectionService.getRowTooltip(
                        vm.row
                    );
                }
            }
            function toggleSelection() {
                selectionService.setRowSelection(
                    vm.row,
                    !selectionService.isRowSelected(vm.row)
                );
            }
        },
    };
});
