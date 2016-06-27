/* globals oneApp, constants */
'use strict';

oneApp.factory('zemGridExportOptions', [function () {

    function getBaseUrl (level, id) {
        if (level === 'all_accounts') {
            return '/api/all_accounts/breakdown/';
        }
        return '/api/' + level + '/' + id + '/';
    }

    function getDefaultOption (options) {
        var defaultOption = options[0];
        for (var i = 1; i < options.length; ++i) {
            if (options[i].defaultOption) {
                defaultOption = options[i];
                break;
            }
        }
        return defaultOption;
    }

    function getOptions (level, breakdown) {
        return [
            {name: 'By Campaign (totals)', value: constants.exportType.CAMPAIGN},
            {name: 'Current View', value: constants.exportType.AD_GROUP, defaultOption: true},
            {name: 'By Content Ad', value: constants.exportType.CONTENT_AD},
        ];
    }

    return {
        getBaseUrl: getBaseUrl,
        getOptions: getOptions,
        getDefaultOption: getDefaultOption,
    };
}]);
