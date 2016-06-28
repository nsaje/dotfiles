/* globals oneApp, constants */
'use strict';

oneApp.directive('zemGridCellStatus', ['zemGridEndpointColumns', function (zemGridEndpointColumns) {

    // Status texts are generated differently for different levels and breakdowns. This function returns an object with
    // row status and list of possible statuses for this row.
    // TODO: Set status object for other levels and breakdowns where status text is available
    // FIXME: constants.adGroupSettingsState.ACTIVE and constants.adGroupSettingsState.INACTIVE are used on "wrong"
    // levels (e.g. enabled and paused value for status on account level is based on constants.adGroupSettingsState)
    function getStatusObject (stats, level, breakdown) {
        var value;
        if (level === constants.level.CAMPAIGNS && breakdown === constants.breakdown.AD_GROUP) {
            if (stats[zemGridEndpointColumns.COLUMNS.stateAdGroup.field]) {
                value = stats[zemGridEndpointColumns.COLUMNS.stateAdGroup.field].value;
            }
            return {
                value: value,
                enabled: constants.adGroupSourceSettingsState.ACTIVE,
                paused: constants.adGroupSourceSettingsState.INACTIVE,
            };
        }
        if (level === constants.level.CAMPAIGNS && breakdown === constants.breakdown.MEDIA_SOURCE) {
            if (stats[zemGridEndpointColumns.COLUMNS.statusMediaSource.field]) {
                value = stats[zemGridEndpointColumns.COLUMNS.statusMediaSource.field].value;
            }
            return {
                value: value,
                enabled: constants.adGroupSettingsState.ACTIVE,
                paused: constants.adGroupSettingsState.INACTIVE,
            };
        }
    }

    function getStatusText (status) {
        if (!status) {
            return '';
        }

        if (status.value === status.enabled) {
            return 'Active';
        } else if (status.value === status.paused) {
            return 'Paused';
        }
        return '';
    }

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            data: '=',
            row: '=',
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_cell_status.html',
        link: function (scope, element, attributes, ctrl) {
            var pubsub = ctrl.grid.meta.pubsub;

            ctrl.statusText = '';

            scope.$watch('ctrl.row', update);
            scope.$watch('ctrl.data', update);
            pubsub.register(pubsub.EVENTS.DATA_UPDATED, update);

            function update () {
                if (ctrl.row) {
                    if (ctrl.row.archived) {
                        ctrl.statusText = 'Archived';
                    } else {
                        var status = getStatusObject(
                            ctrl.row.data.stats,
                            ctrl.grid.meta.data.level,
                            ctrl.grid.meta.data.breakdown
                        );
                        ctrl.statusText = getStatusText(status);
                    }
                }
            }
        },
        controller: [function () {}],
    };
}]);
