/* globals oneApp, constants */
'use strict';

oneApp.factory('zemGridStateAndStatusHelpers', ['zemGridEndpointColumns', function (zemGridEndpointColumns) {
    return {
        getRowStatusObject: getRowStatusObject,
        getAvailableStateValues: getAvailableStateValues,
    };

    // Status texts are generated differently for different levels and breakdowns. This function returns an object with
    // row status and list of possible statuses for this row.
    // TODO: Set status object for other levels and breakdowns where status text is available
    // FIXME: constants.adGroupSettingsState.ACTIVE and constants.adGroupSettingsState.INACTIVE are used on "wrong"
    // levels (e.g. enabled and paused value for status on account level is based on constants.adGroupSettingsState)
    function getRowStatusObject (stats, level, breakdown) {
        if (!stats) {
            return;
        }

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
        if (level === constants.level.AD_GROUPS && breakdown === constants.breakdown.MEDIA_SOURCE) {
            if (stats[zemGridEndpointColumns.COLUMNS.stateMediaSourceAdGroup.field]) {
                value = stats[zemGridEndpointColumns.COLUMNS.stateMediaSourceAdGroup.field].value;
            }
            return {
                value: value,
                enabled: constants.adGroupSettingsState.ACTIVE,
                paused: constants.adGroupSettingsState.INACTIVE,
            };
        }
    }

    function getAvailableStateValues (level, breakdown) {
        // TODO: Set state values for other levels and breakdowns where state selector is available
        if (level === constants.level.CAMPAIGNS && breakdown === constants.breakdown.AD_GROUP) {
            return {
                enabled: constants.adGroupSourceSettingsState.ACTIVE,
                paused: constants.adGroupSourceSettingsState.INACTIVE,
            };
        }
        if (level === constants.level.AD_GROUPS && breakdown === constants.breakdown.MEDIA_SOURCE) {
            return {
                enabled: constants.adGroupSourceSettingsState.ACTIVE,
                paused: constants.adGroupSourceSettingsState.INACTIVE,
            };
        }
        return {enabled: undefined, paused: undefined};
    }
}]);
