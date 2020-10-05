angular
    .module('one.widgets')
    .directive('zemGridCellEditableBaseField', function() {
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
                showAutopilotIcon: '=',
            },
            template: require('./zemGridCellEditableBaseField.component.html'),
            controller: function(
                $scope,
                zemGridConstants,
                zemGridDataFormatter,
                zemGridDataValidator
            ) {
                // eslint-disable-line max-len
                var vm = this;
                var initialValue;
                var prevValidInputValue;

                vm.isSaveRequestInProgress =
                    vm.grid.meta.dataService.isSaveRequestInProgress;
                vm.filterInput = filterInput;
                vm.onKeyDown = onKeyDown;
                vm.save = save;
                vm.closeModal = closeModal;

                $scope.$watch('ctrl.row', update);
                $scope.$watch('ctrl.data', update, true); // TODO: use pubsub for propagating data updates

                function update() {
                    vm.formattedValue = '';
                    vm.isEditable = false;
                    vm.class = vm.column.type + '-field';

                    if (!isFieldVisible()) {
                        return;
                    }

                    var value = vm.data ? vm.data.value : undefined;
                    var formatterOptions = angular.copy(vm.column.data);
                    formatterOptions.currency = vm.grid.meta.data.ext.currency;
                    vm.formattedValue = zemGridDataFormatter.formatValue(
                        value,
                        formatterOptions
                    );
                    vm.currencySymbol = zemGridDataFormatter.getCurrencySymbol(
                        formatterOptions
                    );

                    if (vm.data) {
                        vm.isEditable = vm.data.isEditable;
                        vm.editMessage = vm.data.editMessage;
                    }

                    if (vm.isEditable) {
                        initialValue =
                            zemGridDataFormatter.parseInputValue(
                                value,
                                vm.column.data
                            ) || '';
                        prevValidInputValue = initialValue;
                        vm.editFormInputValue = prevValidInputValue;
                    }
                }

                function isFieldVisible() {
                    if (!vm.row || !vm.column) {
                        return false;
                    }
                    if (
                        vm.row.level === zemGridConstants.gridRowLevel.FOOTER &&
                        vm.column.data.totalRow === false
                    ) {
                        return false;
                    }
                    return true;
                }

                function filterInput() {
                    var options = {
                        type: vm.column.data.type,
                        fractionSize: vm.column.data.fractionSize,
                        maxValue: 999999,
                    };
                    if (
                        zemGridDataValidator.validate(
                            vm.editFormInputValue,
                            options
                        )
                    ) {
                        prevValidInputValue = vm.editFormInputValue;
                    } else {
                        vm.editFormInputValue = prevValidInputValue;
                    }
                }

                function onKeyDown($event) {
                    if ($event.keyCode === 13) save(); // Enter
                    if ($event.keyCode === 27) closeModal(); // ESC
                }

                function save() {
                    if (vm.isSaveRequestInProgress()) {
                        return;
                    }

                    if (prevValidInputValue === initialValue) {
                        closeModal();
                        return;
                    }

                    vm.showLoader = true;
                    vm.errors = [];
                    var value = zemGridDataFormatter.parseInputValue(
                        prevValidInputValue,
                        vm.column.data
                    );

                    vm.grid.meta.dataService
                        .saveData(value, vm.row, vm.column)
                        .then(function() {
                            // FIXME: Revisit after response is refactored on backend
                            vm.showLoader = false;
                            closeModal();
                        })
                        .catch(function(response) {
                            Object.keys(response).forEach(function(key) {
                                var fieldErrors = response[key] || [];
                                fieldErrors.forEach(function(errorMessage) {
                                    vm.errors.push(errorMessage);
                                });
                            });
                            prevValidInputValue = initialValue;
                            vm.editFormInputValue = prevValidInputValue;
                            vm.showLoader = false;
                        });
                }

                function closeModal() {
                    if (vm.modal && vm.modal.close) {
                        vm.modal.close();
                    }
                }
            },
        };
    });
