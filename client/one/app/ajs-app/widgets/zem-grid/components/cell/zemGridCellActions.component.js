angular
    .module('one.widgets')
    .directive('zemGridCellActions', function($timeout) {
        return {
            restrict: 'E',
            replace: true,
            scope: {},
            controllerAs: 'ctrl',
            bindToController: {
                row: '=',
                grid: '=',
            },
            template: require('./zemGridCellActions.component.html'),
            controller: function(
                $scope,
                zemGridConstants,
                zemGridStateAndStatusHelpers,
                zemGridActionsService,
                zemToastsService
            ) {
                // eslint-disable-line max-len
                var vm = this;
                var pubsub = vm.grid.meta.pubsub;
                var previousState;

                var AUTOPILOT_DISABLED_MSG =
                    "To enable this Media Source please increase Autopilot's Daily Spend Cap.";

                vm.stateValues = zemGridStateAndStatusHelpers.getStateValues(
                    vm.grid.meta.data.level,
                    vm.grid.meta.data.breakdown
                );
                vm.toggleState = toggleState;
                vm.isToggleStateInProgress = false;
                vm.execute = execute;

                $scope.$watch('ctrl.row', updateState);
                $scope.$watch('vm.grid.meta.data.ext', updateState);
                pubsub.register(
                    pubsub.EVENTS.ROW_UPDATED,
                    $scope,
                    onRowUpdated
                );
                pubsub.register(
                    pubsub.EVENTS.ROW_UPDATED_ERROR,
                    $scope,
                    onRowUpdatedError
                );

                function onRowUpdated($scope, row) {
                    if (
                        row &&
                        row.breakdownId === vm.row.data.breakdownId &&
                        row.stats.state &&
                        isActive(row.stats.state.value) !== previousState
                    ) {
                        updateState();
                    }
                }

                function onRowUpdatedError($scope, error) {
                    if (
                        error &&
                        error.row &&
                        error.row.data.breakdownId === vm.row.data.breakdownId
                    ) {
                        vm.active = previousState;
                        vm.isToggleStateInProgress = false;
                        var errorMessage = getErrorMessage(error.error);
                        if (errorMessage) {
                            zemToastsService.error(errorMessage);
                        }
                    }
                }

                function updateState() {
                    vm.showLoader = false;
                    vm.isToggleStateInProgress = false;
                    vm.active = false;
                    vm.isEditable = false;
                    vm.enablingAutopilotSourcesAllowed = true;
                    vm.showStateSwitch = false;
                    vm.buttons = [];
                    vm.disabledMessage = '';
                    vm.stateCautionMessage = null;

                    if (vm.row) {
                        vm.enablingAutopilotSourcesAllowed =
                            vm.row.inGroup ||
                            vm.grid.meta.data.ext
                                .enablingAutopilotSourcesAllowed;

                        vm.isFieldVisible = isFieldVisible(vm.row.level);
                        vm.isRowArchived = vm.row.data.archived;
                        vm.showStateSwitch = zemGridActionsService.isStateSwitchVisible(
                            vm.grid.meta.data.level,
                            vm.grid.meta.data.breakdown,
                            vm.row
                        );

                        var buttons = zemGridActionsService.getButtons(
                            vm.grid.meta.data.level,
                            vm.grid.meta.data.breakdown,
                            vm.row
                        );
                        if (
                            buttons.length > 0 &&
                            buttons[0].type !== 'archive' &&
                            vm.grid.meta.data.breakdown !==
                                constants.breakdown.PUBLISHER
                        ) {
                            vm.mainButton = buttons[0];
                            vm.buttons = buttons.slice(1);
                        } else {
                            vm.mainButton = null;
                            vm.buttons = buttons;
                        }

                        if (vm.row.data.stats.state) {
                            var stateData = vm.row.data.stats.state;
                            vm.active = isActive(stateData.value);
                            vm.isEditable = stateData.isEditable;
                            if (stateData.editMessage) {
                                vm.disabledMessage = stateData.editMessage;
                            } else if (
                                !vm.active &&
                                !vm.enablingAutopilotSourcesAllowed
                            ) {
                                vm.disabledMessage = AUTOPILOT_DISABLED_MSG;
                            }
                        }

                        vm.stateCautionMessage = zemGridActionsService.getStateCautionMessage(
                            vm.row
                        );
                    }
                }

                function execute(button) {
                    vm.showLoader = true;
                    button.action(vm.row, vm.grid, button).finally(function() {
                        vm.showLoader = false;
                    });
                    if (button !== vm.mainButton) {
                        vm.modal.close();
                    }
                }

                function toggleState() {
                    if (
                        !vm.isEditable ||
                        (!vm.active && !vm.enablingAutopilotSourcesAllowed) ||
                        vm.isToggleStateInProgress
                    ) {
                        return;
                    }

                    vm.isToggleStateInProgress = true;
                    previousState = vm.active;

                    // Enable CSS transitions to animate the switch-button
                    vm.switchButtonTransitionEnabled = true;

                    var state = vm.active
                        ? vm.stateValues.paused
                        : vm.stateValues.enabled;
                    vm.active = !vm.active;

                    // Disable CSS transitions after toggle animation completes
                    $timeout(function() {
                        vm.switchButtonTransitionEnabled = false;
                    }, 250);

                    vm.grid.meta.dataService.saveDataQueued(state, vm.row, {
                        data: {field: 'state'},
                    });
                }

                function isActive(state) {
                    return state === vm.stateValues.enabled;
                }

                function isFieldVisible(rowLevel) {
                    return rowLevel === zemGridConstants.gridRowLevel.BASE;
                }

                function getErrorMessage(error) {
                    if (!error) {
                        return;
                    }

                    var errorMessage =
                        '[' + vm.row.data.stats.breakdown_name.value + '] ';
                    if (error.state) {
                        errorMessage = errorMessage + error.state[0];
                    } else if (error.cpc) {
                        errorMessage = errorMessage + error.cpc[0];
                    } else if (error.cpm) {
                        errorMessage = errorMessage + error.cpm[0];
                    } else if (error.dailyBudget) {
                        errorMessage = errorMessage + error.dailyBudget[0];
                    } else if (error.data && error.data.message) {
                        errorMessage = errorMessage + error.data.message;
                    } else {
                        errorMessage =
                            errorMessage +
                            'An error occurred. Please try again.';
                    }

                    return errorMessage;
                }
            },
        };
    });
