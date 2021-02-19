require('./zemGridCellActions.component.less');

var commonHelpers = require('../../../../../shared/helpers/common.helpers');

angular
    .module('one.widgets')
    .directive('zemGridCellActions', function($timeout) {
        return {
            restrict: 'E',
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
                zemGridActionsService
            ) {
                // eslint-disable-line max-len
                var vm = this;

                var pubsub;
                var previousState;

                var rowChangeWatchHandler;
                var gridChangeWatchHandler;
                var onRowUpdatedHandler;
                var onRowUpdatedErrorHandler;

                var AUTOPILOT_DISABLED_MSG =
                    "To enable this Media Source please increase Autopilot's Daily Spend Cap.";

                vm.toggleState = toggleState;
                vm.execute = execute;

                vm.$onInit = function() {
                    vm.stateValues = zemGridStateAndStatusHelpers.getStateValues(
                        vm.grid.meta.data.level,
                        vm.grid.meta.data.breakdown
                    );

                    if (
                        vm.grid.meta.renderingEngine ===
                        zemGridConstants.gridRenderingEngineType.CUSTOM_GRID
                    ) {
                        pubsub = vm.grid.meta.pubsub;

                        rowChangeWatchHandler = $scope.$watch(
                            'ctrl.row',
                            updateState
                        );
                        gridChangeWatchHandler = $scope.$watch(
                            'ctrl.grid.meta.data.ext',
                            updateState
                        );

                        onRowUpdatedHandler = pubsub.register(
                            pubsub.EVENTS.ROW_UPDATED,
                            $scope,
                            onRowUpdated
                        );
                        onRowUpdatedErrorHandler = pubsub.register(
                            pubsub.EVENTS.ROW_UPDATED_ERROR,
                            $scope,
                            onRowUpdatedError
                        );
                    }

                    updateState();
                };

                vm.$onDestroy = function() {
                    if (rowChangeWatchHandler) rowChangeWatchHandler();
                    if (gridChangeWatchHandler) gridChangeWatchHandler();
                    if (onRowUpdatedHandler) onRowUpdatedErrorHandler();
                    if (onRowUpdatedErrorHandler) onRowUpdatedErrorHandler();
                };

                // TODO (msuber): remove when migrated to smart-grid
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

                // TODO (msuber): remove when migrated to smart-grid
                function onRowUpdatedError($scope, error) {
                    if (
                        error &&
                        error.row &&
                        error.row.data.breakdownId === vm.row.data.breakdownId
                    ) {
                        vm.active = previousState;
                        vm.isToggleStateInProgress = false;
                    }
                }

                function updateState() {
                    vm.isFieldVisible = false;
                    vm.isToggleStateInProgress = false;
                    vm.active = false;
                    vm.isEditable = false;
                    vm.enablingAutopilotSourcesAllowed = true;
                    vm.showStateSwitch = false;
                    vm.isStateSwitchDisabled = false;
                    vm.buttons = [];
                    vm.disabledMessage = '';
                    vm.stateCautionMessage = null;

                    if (vm.row) {
                        vm.enablingAutopilotSourcesAllowed =
                            vm.row.inGroup ||
                            vm.grid.meta.data.ext
                                .enablingAutopilotSourcesAllowed;

                        vm.isFieldVisible = isFieldVisible(
                            vm.row.level,
                            vm.row.entity
                        );
                        vm.isRowArchived = vm.row.data.archived;
                        vm.showStateSwitch = zemGridActionsService.isStateSwitchVisible(
                            vm.grid.meta.data.level,
                            vm.grid.meta.data.breakdown,
                            vm.row
                        );
                        vm.isStateSwitchDisabled = zemGridActionsService.isStateSwitchDisabled(
                            vm.grid.meta.data.level,
                            vm.grid.meta.data.breakdown,
                            vm.row
                        );

                        var breakdown = getBreakdown(vm.grid, vm.row);
                        var buttons = zemGridActionsService.getButtons(
                            vm.grid.meta.data.level,
                            breakdown,
                            vm.row
                        );
                        if (shouldShowMainButton(buttons)) {
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

                function shouldShowMainButton(buttons) {
                    return (
                        buttons.length > 0 &&
                        buttons[0].type !== 'archive' &&
                        vm.grid.meta.data.breakdown !==
                            constants.breakdown.PUBLISHER &&
                        vm.grid.meta.data.breakdown !==
                            constants.breakdown.PLACEMENT
                    );
                }

                function execute(button) {
                    button.action(vm.row, vm.grid, button).finally(function() {
                        if (button !== vm.mainButton) {
                            vm.modal.close();
                        }
                    });
                }

                function toggleState() {
                    if (
                        !vm.isEditable ||
                        (!vm.active && !vm.enablingAutopilotSourcesAllowed) ||
                        vm.isToggleStateInProgress ||
                        vm.isStateSwitchDisabled
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

                    vm.grid.meta.api.saveDataQueued(state, vm.row, {
                        data: {field: 'state'},
                    });
                }

                function isActive(state) {
                    return state === vm.stateValues.enabled;
                }

                function isFieldVisible(rowLevel, rowEntity) {
                    return (
                        rowLevel === zemGridConstants.gridRowLevel.BASE ||
                        (rowLevel === zemGridConstants.gridRowLevel.LEVEL_2 &&
                            commonHelpers.isDefined(rowEntity) &&
                            (vm.row.entity.type ===
                                constants.entityType.CAMPAIGN ||
                                vm.row.entity.type ===
                                    constants.entityType.AD_GROUP))
                    );
                }

                function getBreakdown(grid, row) {
                    var breakdown = grid.meta.data.breakdown;
                    if (
                        row.level === zemGridConstants.gridRowLevel.LEVEL_2 &&
                        commonHelpers.isDefined(row.entity)
                    ) {
                        if (row.entity.type === constants.entityType.CAMPAIGN) {
                            breakdown = constants.breakdown.CAMPAIGN;
                        } else if (
                            row.entity.type === constants.entityType.AD_GROUP
                        ) {
                            breakdown = constants.breakdown.AD_GROUP;
                        }
                    }
                    return breakdown;
                }
            },
        };
    });
