angular
    .module('one.widgets')
    .factory('zemGridStateAndStatusHelpers', function() {
        return {
            getStatusValuesAndTexts: getStatusValuesAndTexts,
            getStateValues: getStateValues,
        };

        // FIXME: Change constants used for different level/breakdown combinations
        // prettier-ignore
        function getStatusValuesAndTexts(level, breakdown) { // eslint-disable-line complexity
            var statusTexts;
            if (
                level === constants.level.ALL_ACCOUNTS &&
                breakdown === constants.breakdown.ACCOUNT
            ) {
                statusTexts = {};
                statusTexts[constants.settingsState.ACTIVE] = 'Active';
                statusTexts[constants.settingsState.INACTIVE] = 'Paused';

                return {
                    enabled: constants.settingsState.ACTIVE,
                    paused: constants.settingsState.INACTIVE,
                    statusTexts: statusTexts,
                };
            }
            if (
                level === constants.level.ACCOUNTS &&
                breakdown === constants.breakdown.CAMPAIGN
            ) {
                statusTexts = {};
                statusTexts[constants.settingsState.ACTIVE] = 'Active';
                statusTexts[constants.settingsState.INACTIVE] = 'Paused';

                return {
                    enabled: constants.settingsState.ACTIVE,
                    paused: constants.settingsState.INACTIVE,
                    statusTexts: statusTexts,
                };
            }
            if (
                level === constants.level.CAMPAIGNS &&
                breakdown === constants.breakdown.AD_GROUP
            ) {
                statusTexts = {};
                statusTexts[constants.settingsState.ACTIVE] = 'Active';
                statusTexts[constants.settingsState.INACTIVE] = 'Paused';

                return {
                    enabled: constants.settingsState.ACTIVE,
                    paused: constants.settingsState.INACTIVE,
                    statusTexts: statusTexts,
                };
            }
            if (
                level === constants.level.AD_GROUPS &&
                breakdown === constants.breakdown.CONTENT_AD
            ) {
                statusTexts = {};
                statusTexts[constants.settingsState.ACTIVE] = 'Active';
                statusTexts[constants.settingsState.INACTIVE] = 'Paused';

                return {
                    enabled: constants.settingsState.ACTIVE,
                    paused: constants.settingsState.INACTIVE,
                    statusTexts: statusTexts,
                };
            }
            if (
                level === constants.level.ALL_ACCOUNTS &&
                breakdown === constants.breakdown.MEDIA_SOURCE
            ) {
                statusTexts = {};
                statusTexts[constants.settingsState.ACTIVE] = 'Active';
                statusTexts[constants.settingsState.INACTIVE] = 'Paused';

                return {
                    enabled: constants.settingsState.ACTIVE,
                    paused: constants.settingsState.INACTIVE,
                    statusTexts: statusTexts,
                };
            }
            if (
                level === constants.level.ACCOUNTS &&
                breakdown === constants.breakdown.MEDIA_SOURCE
            ) {
                statusTexts = {};
                statusTexts[constants.settingsState.ACTIVE] = 'Active';
                statusTexts[constants.settingsState.INACTIVE] = 'Paused';

                return {
                    enabled: constants.settingsState.ACTIVE,
                    paused: constants.settingsState.INACTIVE,
                    statusTexts: statusTexts,
                };
            }
            if (
                level === constants.level.CAMPAIGNS &&
                breakdown === constants.breakdown.MEDIA_SOURCE
            ) {
                statusTexts = {};
                statusTexts[constants.settingsState.ACTIVE] = 'Active';
                statusTexts[constants.settingsState.INACTIVE] = 'Paused';

                return {
                    enabled: constants.settingsState.ACTIVE,
                    paused: constants.settingsState.INACTIVE,
                    statusTexts: statusTexts,
                };
            }
            if (
                level === constants.level.AD_GROUPS &&
                breakdown === constants.breakdown.MEDIA_SOURCE
            ) {
                statusTexts = {};
                statusTexts[constants.settingsState.ACTIVE] = 'Active';
                statusTexts[constants.settingsState.INACTIVE] = 'Paused';

                return {
                    enabled: constants.settingsState.ACTIVE,
                    paused: constants.settingsState.INACTIVE,
                    statusTexts: statusTexts,
                };
            }
            if (breakdown === constants.breakdown.PUBLISHER) {
                statusTexts = {};
                statusTexts[constants.publisherTargetingStatus.UNLISTED] =
                    'Active';
                statusTexts[constants.publisherTargetingStatus.BLACKLISTED] =
                    'Blacklisted';
                statusTexts[constants.publisherTargetingStatus.WHITELISTED] =
                    'Whitelisted';

                return {
                    unlisted: constants.publisherTargetingStatus.UNLISTED,
                    blacklisted: constants.publisherTargetingStatus.BLACKLISTED,
                    whitelisted: constants.publisherTargetingStatus.WHITELISTED,
                    statusTexts: statusTexts,
                };
            }
            if (breakdown === constants.breakdown.PLACEMENT) {
                statusTexts = {};
                statusTexts[constants.publisherTargetingStatus.UNLISTED] =
                    'Active';
                statusTexts[constants.publisherTargetingStatus.BLACKLISTED] =
                    'Blacklisted';
                statusTexts[constants.publisherTargetingStatus.WHITELISTED] =
                    'Whitelisted';

                return {
                    unlisted: constants.publisherTargetingStatus.UNLISTED,
                    blacklisted: constants.publisherTargetingStatus.BLACKLISTED,
                    whitelisted: constants.publisherTargetingStatus.WHITELISTED,
                    statusTexts: statusTexts,
                };
            }
        }

        function getStateValues(level, breakdown) {
            // FIXME: Change constants used for different level/breakdown combinations
            if (
                level === constants.level.CAMPAIGNS &&
                breakdown === constants.breakdown.AD_GROUP
            ) {
                return {
                    enabled: constants.settingsState.ACTIVE,
                    paused: constants.settingsState.INACTIVE,
                };
            }
            if (
                level === constants.level.AD_GROUPS &&
                breakdown === constants.breakdown.CONTENT_AD
            ) {
                return {
                    enabled: constants.settingsState.ACTIVE,
                    paused: constants.settingsState.INACTIVE,
                };
            }
            if (
                level === constants.level.AD_GROUPS &&
                breakdown === constants.breakdown.MEDIA_SOURCE
            ) {
                return {
                    enabled: constants.settingsState.ACTIVE,
                    paused: constants.settingsState.INACTIVE,
                };
            }
            return {enabled: undefined, paused: undefined};
        }
    });
