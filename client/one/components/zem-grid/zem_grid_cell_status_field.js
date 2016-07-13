/* globals oneApp, constants */
'use strict';

oneApp.directive('zemGridCellStatusField', ['zemGridEndpointColumns', function (zemGridEndpointColumns) {

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
        templateUrl: '/components/zem-grid/templates/zem_grid_cell_status_field.html',
        controller: ['$scope', function ($scope) {
            var vm = this;
            var pubsub = vm.grid.meta.pubsub;

            $scope.$watch('ctrl.row', update);
            $scope.$watch('ctrl.data', update);
            pubsub.register(pubsub.EVENTS.DATA_UPDATED, update);

            function update () {
                vm.statusText = '';

                if (vm.row) {
                    if (vm.row.archived) {
                        vm.statusText = 'Archived';
                    } else {
                        var status = getStatusObject(
                            vm.row.data.stats,
                            vm.grid.meta.data.level,
                            vm.grid.meta.data.breakdown
                        );
                        vm.statusText = getStatusText(status);
                    }
                }
            }
        }],
    };
}]);
