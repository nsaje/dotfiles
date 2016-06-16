/* globals oneApp, constants */
'use strict';

oneApp.factory('zemGridEndpointApi', ['api', 'zemGridEndpointColumns', function (api, zemGridEndpointColumns) { // eslint-disable-line max-len
    //
    // Service responsible for defining API methods used by Grid Endpoint
    // based on level, breakdown and field -> uniquely defines table and column/field
    // Each specific API contains CRUD functions that are supported on specific field (e.g. save)
    // Function signature - function (levelEntityId, breakdownEntityId, value) [returns Promise]
    //      - levelEntityId --> ID of entity on which we made breakdown
    //      - breakdownEntityId --> ID of one instance in breakdown list
    //      - value (optional) --> new value to be propagated (for save)
    //
    var COLUMNS = zemGridEndpointColumns.COLUMNS;

    function CampaignsAdGroupState () {
        this.save = function (levelEntityId, breakdownEntityId, value) {
            return api.adGroupContentAdState.post(levelEntityId, value, [breakdownEntityId]);
        };
    }

    AdGroupsContentAdState.SUPPORTED_FIELDS = [COLUMNS.bidCpcSetting.field, COLUMNS.dailyBudgetSetting.field];
    function AdGroupsContentAdState () {
        this.save = function (levelEntityId, breakdownEntityId, value) {
            return api.adGroupSettingsState.post(breakdownEntityId, value);
        };
    }

    function AdGroupsSourceSettings (field) {
        this.save = function (levelEntityId, breakdownEntityId, value) {
            var settings = {};
            settings[field] = value;
            return api.adGroupSettingsState.post(levelEntityId, settings);
        };
    }

    function getApi (level, breakdown, field) {
        if (level === constants.level.AD_GROUPS && breakdown === constants.breakdown.MEDIA_SOURCE) {
            if (AdGroupsSourceSettings.SUPPORTED_FIELDS.indexOf(field) >= 0) {
                return new AdGroupsSourceSettings(field);
            }
        }

        if (level === constants.level.CAMPAIGNS &&
            breakdown === constants.breakdown.AD_GROUP &&
            field === COLUMNS.stateAdGroup.field) {
            return new CampaignsAdGroupState();
        }

        if (level === constants.level.AD_GROUPS &&
            breakdown === constants.breakdown.CONTENT_AD &&
            field === COLUMNS.stateAdGroup.field) {
            return new CampaignsAdGroupState();
        }
    }

    return {
        getApi: getApi,
    };
}]);
