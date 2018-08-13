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

                var AUTOPILOT_DISABLED_MSG =
                    "To enable this Media Source please increase Autopilot's Daily Spend Cap.";

                vm.isSaveRequestInProgress =
                    vm.grid.meta.dataService.isSaveRequestInProgress;
                vm.stateValues = zemGridStateAndStatusHelpers.getStateValues(
                    vm.grid.meta.data.level,
                    vm.grid.meta.data.breakdown
                );
                vm.toggleState = toggleState;
                vm.execute = execute;

                $scope.$watch('ctrl.row', update);
                $scope.$watch('vm.grid.meta.data.ext', update);
                pubsub.register(pubsub.EVENTS.DATA_UPDATED, $scope, update);

                function update() {
                    vm.showLoader = false;
                    vm.active = false;
                    vm.isEditable = false;
                    vm.enablingAutopilotSourcesAllowed = true;
                    vm.showStateSwitch = false;
                    vm.buttons = [];
                    vm.disabledMessage = '';

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
                        (!vm.active && !vm.enablingAutopilotSourcesAllowed)
                    ) {
                        return;
                    }

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

                    vm.grid.meta.dataService
                        .saveData(state, vm.row, {data: {field: 'state'}})
                        .catch(function(data) {
                            if (!data) {
                                return;
                            }
                            if (data.state) {
                                zemToastsService.error(data.state);
                            } else if (data.data && data.data.message) {
                                zemToastsService.error(data.data.message);
                            }
                        })
                        .finally(function() {
                            update();
                        });
                }

                function isActive(state) {
                    return state === vm.stateValues.enabled;
                }

                function isFieldVisible(rowLevel) {
                    return rowLevel === zemGridConstants.gridRowLevel.BASE;
                }
            },
        };
    });
