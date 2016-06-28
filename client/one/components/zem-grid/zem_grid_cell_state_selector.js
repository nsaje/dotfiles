/* globals oneApp, constants */
'use strict';

oneApp.directive('zemGridCellStateSelector', [function () {

    function getStateValues (level, breakdown) {
        // TODO: Set state values for other levels and breakdowns where state selector is available
        if (level === constants.level.CAMPAIGNS && breakdown === constants.breakdown.AD_GROUP) {
            return {
                enabled: constants.adGroupSourceSettingsState.ACTIVE,
                paused: constants.adGroupSourceSettingsState.INACTIVE,
            };
        }
        return {enabled: undefined, paused: undefined};
    }

    function isActive (state, enabledState) {
        return state === enabledState;
    }

    function isFieldVisible (rowLevel) {
        return rowLevel === 1;
    }

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
        link: function (scope, element, attributes, ctrl) {
            ctrl.stateValues = getStateValues(ctrl.grid.meta.data.level, ctrl.grid.meta.data.breakdown);
            ctrl.setState = setState;

            scope.$watch('ctrl.row', update);
            scope.$watch('ctrl.data', update);

            function update () {
                // TODO: Save loader visibility to row object so that it is not reset for this row when DOM element is
                // reused to display different row
                ctrl.showLoader = false;
                ctrl.active = false;
                ctrl.isEditable = false;
                ctrl.enablingAutopilotSourcesAllowed = ctrl.grid.meta.data.enablingAutopilotSourcesAllowed;

                if (ctrl.row) {
                    ctrl.isFieldVisible = isFieldVisible(ctrl.row.level);
                    ctrl.isRowArchived = ctrl.row.data.archived;
                }
                if (ctrl.data) {
                    ctrl.active = isActive(ctrl.data.value, ctrl.stateValues.enabled);
                    ctrl.isEditable = ctrl.data.isEditable;
                    ctrl.disabledMessage = ctrl.data.editMessage;
                }
            }

            function setState (state) {
                // Prevent enabling source when editing is not allowed or when enabling not allowed by the autopilot
                if (!ctrl.isEditable || !ctrl.active && !ctrl.enablingAutopilotSourcesAllowed) {
                    closeStateSelectorModal();
                    return;
                }

                // Do nothing when no change
                if (state === ctrl.data.value) {
                    closeStateSelectorModal();
                    return;
                }

                ctrl.showLoader = true;
                closeStateSelectorModal();

                ctrl.grid.meta.service.saveData(state, ctrl.row, ctrl.column)
                .then(function () {
                    update();
                    ctrl.showLoader = false;
                })
                .catch(function () {
                    ctrl.showLoader = false;
                });
            }

            function closeStateSelectorModal () {
                if (ctrl.modal && ctrl.modal.close) {
                    ctrl.modal.close();
                }
            }
        },
        controller: [function () {}],
    };
}]);
