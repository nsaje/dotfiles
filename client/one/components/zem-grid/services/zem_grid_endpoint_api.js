/* globals oneApp, constants */
'use strict';

oneApp.factory('zemGridEndpointApi', ['$q', 'api', 'zemGridEndpointColumns', function ($q, api, zemGridEndpointColumns) { // eslint-disable-line max-len
    //
    // Service responsible for defining API methods used by Grid Endpoint based on
    // level, breakdown and column -> uniquely defines table cells throughout the application
    // Each specific API contains CRUD functions that are supported on specific field (e.g. save)
    // Function signature - function (levelEntityId, breakdownEntityId, value) [returns Promise]
    //      - levelEntityId --> ID of entity on which we made breakdown
    //      - breakdownEntityId --> ID of one instance in breakdown list
    //      - value (optional) --> new value to be propagated (for save)
    //
    var COLUMNS = zemGridEndpointColumns.COLUMNS;

    function CampaignsAdGroupState () {
        this.save = function (levelEntityId, breakdownEntityId, value) {
            var deferred = $q.defer();
            api.adGroupSettingsState.post(breakdownEntityId, value).then(function (data) {
                data['state'] = {value: data['state']};
                deferred.resolve(data);
            }, function (err) {
                deferred.reject(err);
            });
            return deferred.promise;
        };
    }

    function AdGroupsContentAdState () {
        this.save = function (levelEntityId, breakdownEntityId, value) {
            return api.adGroupContentAdState.save(levelEntityId, value, [breakdownEntityId]);
        };
    }

    AdGroupsSourceSettings.SUPPORTED_FIELDS = [COLUMNS.bidCpcSetting.field, COLUMNS.dailyBudgetSetting.field];
    function AdGroupsSourceSettings (key) {
        this.save = function (levelEntityId, breakdownEntityId, value) {
            var settings = convertToApi(key, value);
            return api.adGroupSourceSettings.save(levelEntityId, breakdownEntityId, settings);
        };

        function convertToApi (key, value) {
            var settings = {};
            switch (key) {
            case COLUMNS.bidCpcSetting.field:
                settings['cpc_cc'] = value;
                break;
            case COLUMNS.dailyBudgetSetting.field:
                settings['daily_budget_cc'] = value;
                break;
            default: settings[key] = value;
            }
            return settings;
        }
    }

    function getApi (level, breakdown, column) {
        if (level === constants.level.AD_GROUPS && breakdown === constants.breakdown.MEDIA_SOURCE) {
            if (AdGroupsSourceSettings.SUPPORTED_FIELDS.indexOf(column.field) >= 0) {
                return new AdGroupsSourceSettings(column.field);
            }
        }

        if (level === constants.level.CAMPAIGNS &&
            breakdown === constants.breakdown.AD_GROUP &&
            column.field === COLUMNS.state.field) {
            return new CampaignsAdGroupState();
        }

        if (level === constants.level.AD_GROUPS &&
            breakdown === constants.breakdown.CONTENT_AD &&
            column.field === COLUMNS.state.field) {
            return new AdGroupsContentAdState();
        }
    }

    return {
        getApi: getApi,
    };
}]);
