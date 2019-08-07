angular.module('one.widgets').directive('zemGridCell', function() {
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            col: '=',
            data: '=',
            row: '=',
            grid: '=',
        },
        template: require('./zemGridCell.component.html'),
        controller: function(
            $scope,
            zemGridConstants,
            zemGridEndpointColumns,
            zemGridStateAndStatusHelpers
        ) {
            var ctrl = this;
            ctrl.gridColumnTypes = zemGridConstants.gridColumnTypes;
            ctrl.type = getFieldType();
            ctrl.gridBodyElement = getGridBodyElement();
            ctrl.showAutopilotIcon = isAutopilotIconShown();
            ctrl.canSeePublisherBidModifierCell = canSeePublisherBidModifierCell;
            ctrl.canSeeBidModifierCell = canSeeBidModifierCell;
            ctrl.updateBidModifier = updateBidModifier;
            var stateValues = zemGridStateAndStatusHelpers.getStateValues(
                ctrl.grid.meta.data.level,
                ctrl.grid.meta.data.breakdown
            );

            $scope.$watch('ctrl.col', function() {
                ctrl.type = getFieldType();
                ctrl.showAutopilotIcon = isAutopilotIconShown();
            });

            $scope.$watch('ctrl.data', function() {
                ctrl.showAutopilotIcon = isAutopilotIconShown();
            });

            function getFieldType() {
                if (!ctrl.col) {
                    return zemGridConstants.gridColumnTypes.BASE_FIELD;
                }

                var columnType =
                    ctrl.col.type ||
                    zemGridConstants.gridColumnTypes.BASE_FIELD;

                if (
                    zemGridConstants.gridColumnTypes.BASE_TYPES.indexOf(
                        columnType
                    ) !== -1
                ) {
                    if (ctrl.col.data && ctrl.col.data.editable) {
                        return zemGridConstants.gridColumnTypes
                            .EDITABLE_BASE_FIELD;
                    }
                    return zemGridConstants.gridColumnTypes.BASE_FIELD;
                }

                if (
                    zemGridConstants.gridColumnTypes.EXTERNAL_LINK_TYPES.indexOf(
                        columnType
                    ) !== -1
                ) {
                    return zemGridConstants.gridColumnTypes.EXTERNAL_LINK;
                }

                return columnType;
            }

            function getGridBodyElement() {
                if (ctrl.grid) {
                    return ctrl.grid.body.ui.element[0];
                }
            }

            function canSeePublisherBidModifierCell() {
                if (
                    !ctrl.row ||
                    ctrl.row.level === zemGridConstants.gridRowLevel.FOOTER
                ) {
                    return false;
                }

                if (!ctrl.data || !ctrl.data.value) {
                    return false;
                }

                return (
                    getFieldType() ===
                        zemGridConstants.gridColumnTypes.BID_MODIFIER_FIELD &&
                    ctrl.grid.meta.data.breakdown ===
                        constants.breakdown.PUBLISHER
                );
            }

            function canSeeBidModifierCell() {
                if (
                    !ctrl.row ||
                    ctrl.row.level === zemGridConstants.gridRowLevel.FOOTER
                ) {
                    return false;
                }

                if (!ctrl.data || !ctrl.data.value) {
                    return false;
                }

                return (
                    ctrl.type ===
                        zemGridConstants.gridColumnTypes.BID_MODIFIER_FIELD &&
                    ctrl.grid.meta.data.breakdown !==
                        constants.breakdown.PUBLISHER
                );
            }

            function isAutopilotIconShown() {
                if (ctrl.data && !ctrl.data.value) {
                    return false;
                }
                if (ctrl.grid.meta.data.campaignAutopilot) {
                    return isRowActive();
                }
                if (
                    ctrl.grid.meta.data.adGroupAutopilotState ===
                    constants.adGroupSettingsAutopilotState.INACTIVE
                ) {
                    return false;
                }
                if (
                    ctrl.grid.meta.data.adGroupAutopilotState ===
                        constants.adGroupSettingsAutopilotState.ACTIVE_CPC &&
                    ctrl.col.field ===
                        zemGridEndpointColumns.COLUMNS.dailyBudgetSetting.field
                ) {
                    return false;
                }
                return isRowActive();
            }

            function isRowActive() {
                if (!ctrl.row || ctrl.row.archived) {
                    return false;
                }

                var rowState;
                if (
                    ctrl.row.data &&
                    ctrl.row.data.stats &&
                    ctrl.row.data.stats.state
                ) {
                    rowState = ctrl.row.data.stats.state.value;
                }

                if (!stateValues || rowState !== stateValues.enabled) {
                    return false;
                }

                return true;
            }

            function updateBidModifier($event) {
                ctrl.data.value = $event;
            }
        },
    };
});
