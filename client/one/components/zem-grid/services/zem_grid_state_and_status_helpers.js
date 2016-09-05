/* globals angular, constants */
'use strict';

angular.module('one.legacy').factory('zemGridStateAndStatusHelpers', ['zemGridEndpointColumns', function (zemGridEndpointColumns) {
    return {
        getStatusValuesAndTexts: getStatusValuesAndTexts,
        getStateValues: getStateValues,
    };

    // FIXME: Change constants used for different level/breakdown combinations
    function getStatusValuesAndTexts (level, breakdown) {
        var statusTexts;
        if (level === constants.level.ALL_ACCOUNTS && breakdown === constants.breakdown.ACCOUNT) {
            statusTexts = {};
            statusTexts[constants.adGroupSettingsState.ACTIVE] = 'Active';
            statusTexts[constants.adGroupSettingsState.INACTIVE] = 'Paused';

            return {
                enabled: constants.adGroupSettingsState.ACTIVE,
                paused: constants.adGroupSettingsState.INACTIVE,
                statusTexts: statusTexts,
            };
        }
        if (level === constants.level.ACCOUNTS && breakdown === constants.breakdown.CAMPAIGN) {
            statusTexts = {};
            statusTexts[constants.adGroupSettingsState.ACTIVE] = 'Active';
            statusTexts[constants.adGroupSettingsState.INACTIVE] = 'Paused';

            return {
                enabled: constants.adGroupSettingsState.ACTIVE,
                paused: constants.adGroupSettingsState.INACTIVE,
                statusTexts: statusTexts,
            };
        }
        if (level === constants.level.CAMPAIGNS && breakdown === constants.breakdown.AD_GROUP) {
            statusTexts = {};
            statusTexts[constants.adGroupSourceSettingsState.ACTIVE] = 'Active';
            statusTexts[constants.adGroupSourceSettingsState.INACTIVE] = 'Paused';

            return {
                enabled: constants.adGroupSourceSettingsState.ACTIVE,
                paused: constants.adGroupSourceSettingsState.INACTIVE,
                statusTexts: statusTexts,
            };
        }
        if (level === constants.level.AD_GROUPS && breakdown === constants.breakdown.CONTENT_AD) {
            statusTexts = {};
            statusTexts[constants.adGroupSettingsState.ACTIVE] = 'Active';
            statusTexts[constants.adGroupSettingsState.INACTIVE] = 'Paused';

            return {
                enabled: constants.adGroupSettingsState.ACTIVE,
                paused: constants.adGroupSettingsState.INACTIVE,
                statusTexts: statusTexts,
            };
        }
        if (level === constants.level.ALL_ACCOUNTS && breakdown === constants.breakdown.MEDIA_SOURCE) {
            statusTexts = {};
            statusTexts[constants.adGroupSettingsState.ACTIVE] = 'Active';
            statusTexts[constants.adGroupSettingsState.INACTIVE] = 'Paused';

            return {
                enabled: constants.adGroupSettingsState.ACTIVE,
                paused: constants.adGroupSettingsState.INACTIVE,
                statusTexts: statusTexts,
            };
        }
        if (level === constants.level.ACCOUNTS && breakdown === constants.breakdown.MEDIA_SOURCE) {
            statusTexts = {};
            statusTexts[constants.adGroupSettingsState.ACTIVE] = 'Active';
            statusTexts[constants.adGroupSettingsState.INACTIVE] = 'Paused';

            return {
                enabled: constants.adGroupSettingsState.ACTIVE,
                paused: constants.adGroupSettingsState.INACTIVE,
                statusTexts: statusTexts,
            };
        }
        if (level === constants.level.CAMPAIGNS && breakdown === constants.breakdown.MEDIA_SOURCE) {
            statusTexts = {};
            statusTexts[constants.adGroupSettingsState.ACTIVE] = 'Active';
            statusTexts[constants.adGroupSettingsState.INACTIVE] = 'Paused';

            return {
                enabled: constants.adGroupSettingsState.ACTIVE,
                paused: constants.adGroupSettingsState.INACTIVE,
                statusTexts: statusTexts,
            };
        }
        if (level === constants.level.AD_GROUPS && breakdown === constants.breakdown.MEDIA_SOURCE) {
            statusTexts = {};
            statusTexts[constants.adGroupSettingsState.ACTIVE] = 'Active';
            statusTexts[constants.adGroupSettingsState.INACTIVE] = 'Paused';

            return {
                enabled: constants.adGroupSettingsState.ACTIVE,
                paused: constants.adGroupSettingsState.INACTIVE,
                statusTexts: statusTexts,
            };
        }
        if (level === constants.level.AD_GROUPS && breakdown === constants.breakdown.PUBLISHER) {
            statusTexts = {};
            statusTexts[constants.publisherStatus.ENABLED] = 'Active';
            statusTexts[constants.publisherStatus.BLACKLISTED] = 'Blacklisted';
            statusTexts[constants.publisherStatus.PENDING] = 'Pending';

            return {
                enabled: constants.publisherStatus.ENABLED,
                blacklisted: constants.publisherStatus.BLACKLISTED,
                pending: constants.publisherStatus.PENDING,
                statusTexts: statusTexts,
            };
        }
    }

    function getStateValues (level, breakdown) {
        // FIXME: Change constants used for different level/breakdown combinations
        if (level === constants.level.CAMPAIGNS && breakdown === constants.breakdown.AD_GROUP) {
            return {
                enabled: constants.adGroupSourceSettingsState.ACTIVE,
                paused: constants.adGroupSourceSettingsState.INACTIVE,
            };
        }
        if (level === constants.level.AD_GROUPS && breakdown === constants.breakdown.CONTENT_AD) {
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
