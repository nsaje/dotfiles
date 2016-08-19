/* globals oneApp, constants */
'use strict';

oneApp.directive('zemGridCellEditableBaseField', [function () {

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
        templateUrl: '/components/zem-grid/templates/zem_grid_cell_editable_base_field.html',
        controller: ['$scope', 'zemGridConstants', 'zemGridDataFormatter', 'zemGridDataValidator', 'zemGridStateAndStatusHelpers', function ($scope, zemGridConstants, zemGridDataFormatter, zemGridDataValidator, zemGridStateAndStatusHelpers) { // eslint-disable-line max-len
            var vm = this;
            var initialValue;
            var prevValidInputValue;
            var stateValues = zemGridStateAndStatusHelpers.getStateValues(
                vm.grid.meta.data.level, vm.grid.meta.data.breakdown
            );

            vm.isSaveRequestInProgress = vm.grid.meta.dataService.isSaveRequestInProgress;
            vm.isAutopilotIconShown = isAutopilotIconShown;
            vm.filterInput = filterInput;
            vm.onKeyDown = onKeyDown;
            vm.save = save;
            vm.closeModal = closeModal;

            $scope.$watch('ctrl.row', update);
            $scope.$watch('ctrl.data', update, true); // TODO: use pubsub for propagating data updates

            function update () {
                vm.formattedValue = '';
                vm.isEditable = false;
                vm.class = vm.column.type + '-field';

                if (!isFieldVisible()) {
                    return;
                }

                var value = vm.data ? vm.data.value : undefined;
                vm.formattedValue = zemGridDataFormatter.formatValue(value, vm.column.data);

                if (vm.data) {
                    vm.isEditable = vm.data.isEditable;
                    vm.editMessage = vm.data.editMessage;
                }

                if (vm.isEditable) {
                    initialValue = zemGridDataFormatter.parseInputValue(value, vm.column.data) || '';
                    prevValidInputValue = initialValue;
                    vm.editFormInputValue = prevValidInputValue;
                }
            }

            function isFieldVisible () {
                if (!vm.row || !vm.column) {
                    return false;
                }
                if (vm.row.level === zemGridConstants.gridRowLevel.FOOTER && vm.column.data.totalRow === false) {
                    return false;
                }
                return true;
            }

            function isAutopilotIconShown () {
                if (vm.grid.meta.data.adGroupAutopilotState === constants.adGroupSettingsAutopilotState.INACTIVE) {
                    return false;
                }
                return isRowActive();
            }

            function isRowActive () {
                if (!vm.row || vm.row.archived) {
                    return false;
                }

                var rowState;
                if (vm.row.data && vm.row.data.stats && vm.row.data.stats.state) {
                    rowState = vm.row.data.stats.state.value;
                }

                if (!stateValues || rowState !== stateValues.enabled) {
                    return false;
                }

                return true;
            }

            function filterInput () {
                if (zemGridDataValidator.validate(vm.editFormInputValue, vm.column.data)) {
                    prevValidInputValue = vm.editFormInputValue;
                } else {
                    vm.editFormInputValue = prevValidInputValue;
                }
            }

            function onKeyDown ($event) {
                if ($event.keyCode === 13) save();  // Enter
                if ($event.keyCode === 27) closeModal(); // ESC
            }

            function save () {
                if (vm.isSaveRequestInProgress()) {
                    return;
                }

                if (prevValidInputValue === initialValue) {
                    closeModal();
                    return;
                }

                vm.showLoader = true;
                vm.errors = [];
                var value = zemGridDataFormatter.parseInputValue(prevValidInputValue, vm.column.data);

                vm.grid.meta.dataService.saveData(value, vm.row, vm.column)
                .then(function () {
                    // FIXME: Revisit after response is refactored on backend
                    vm.showLoader = false;
                    closeModal();
                })
                .catch(function (response) {
                    Object.keys(response).forEach(function (key) {
                        var fieldErrors = response[key] || [];
                        fieldErrors.forEach(function (errorMessage) {
                            vm.errors.push(errorMessage);
                        });
                    });
                    prevValidInputValue = initialValue;
                    vm.editFormInputValue = prevValidInputValue;
                    vm.showLoader = false;
                });
            }

            function closeModal () {
                if (vm.modal && vm.modal.close) {
                    vm.modal.close();
                }
            }
        }],
    };
}]);
