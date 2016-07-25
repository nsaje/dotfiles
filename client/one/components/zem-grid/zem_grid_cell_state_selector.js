/* globals oneApp, constants */
'use strict';

oneApp.directive('zemGridCellStateSelector', [function () {

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
        templateUrl: '/components/zem-grid/templates/zem_grid_cell_state_selector.html',
        controller: ['$scope', 'zemGridConstants', 'zemGridStateAndStatusHelpers', function ($scope, zemGridConstants, zemGridStateAndStatusHelpers) { // eslint-disable-line max-len
            var vm = this;

            vm.stateValues = zemGridStateAndStatusHelpers.getAvailableStateValues(vm.grid.meta.data.level, vm.grid.meta.data.breakdown);
            vm.setState = setState;

            $scope.$watch('ctrl.row', update);
            $scope.$watch('ctrl.data', update);

            function update () {
                // TODO: Save loader visibility to row object so that it is not reset for this row when DOM element is
                // reused to display different row
                vm.showLoader = false;
                vm.active = false;
                vm.isEditable = false;
                vm.enablingAutopilotSourcesAllowed = vm.grid.meta.data.ext.enablingAutopilotSourcesAllowed;

                if (vm.row) {
                    vm.isFieldVisible = isFieldVisible(vm.row.level);
                    vm.isRowArchived = vm.row.data.archived;
                }
                if (vm.data) {
                    vm.active = isActive(vm.data.value, vm.stateValues.enabled);
                    vm.isEditable = vm.data.isEditable;
                    vm.disabledMessage = vm.data.editMessage;
                }
            }

            function setState (state) {
                // Prevent enabling source when editing is not allowed or when enabling not allowed by the autopilot
                if (!vm.isEditable || !vm.active && !vm.enablingAutopilotSourcesAllowed) {
                    closeStateSelectorModal();
                    return;
                }

                // Do nothing when no change
                if (state === vm.data.value) {
                    closeStateSelectorModal();
                    return;
                }

                vm.showLoader = true;
                closeStateSelectorModal();

                vm.grid.meta.dataService.saveData(state, vm.row, vm.column)
                .then(function () {
                    update();
                    vm.showLoader = false;
                })
                .catch(function () {
                    vm.showLoader = false;
                });
            }

            function closeStateSelectorModal () {
                if (vm.modal && vm.modal.close) {
                    vm.modal.close();
                }
            }

            function isActive (state, enabledState) {
                return state === enabledState;
            }

            function isFieldVisible (rowLevel) {
                return rowLevel === zemGridConstants.gridRowLevel.BASE;
            }
        }],
    };
}]);
