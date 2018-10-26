angular.module('one.widgets').factory('zemGridExportOptions', function() {
    // //////////////////////////////////////////////////////////////////////////////////////////////////
    // EXPORT OPTIONS DEFINITIONS
    //
    var OPTIONS = {
        allAccounts: {
            name: 'By All Accounts',
            value: constants.exportType.ALL_ACCOUNTS,
        },
        account: {name: 'By Account', value: constants.exportType.ACCOUNT},
        campaign: {name: 'By Campaign', value: constants.exportType.CAMPAIGN},
        adGroup: {name: 'By Ad Group', value: constants.exportType.AD_GROUP},
        contentAd: {
            name: 'By Content Ad',
            value: constants.exportType.CONTENT_AD,
        },
    };

    var ALL_ACCOUNTS_LEVEL_OPTIONS = [
        OPTIONS.allAccounts,
        OPTIONS.account,
        OPTIONS.campaign,
        OPTIONS.adGroup,
    ];

    var ACCOUNTS_LEVEL_OPTIONS = [
        OPTIONS.account,
        OPTIONS.campaign,
        OPTIONS.adGroup,
        OPTIONS.contentAd,
    ];

    var CAMPAIGNS_LEVEL_OPTIONS = [
        OPTIONS.campaign,
        OPTIONS.adGroup,
        OPTIONS.contentAd,
    ];

    var AD_GROUPS_LEVEL_OPTIONS = [OPTIONS.adGroup, OPTIONS.contentAd];

    // ///////////////////////////////////////////////////////////////////////////////////////////////////
    // Service functions
    //

    function getBaseUrl(level, breakdown, id) {
        var baseUrl = '/api/' + level + '/';
        if (level !== constants.level.ALL_ACCOUNTS) {
            baseUrl += id + '/';
        }

        if (breakdown === constants.breakdown.MEDIA_SOURCE) {
            baseUrl += 'sources/';
        }

        return baseUrl;
    }

    function getDefaultOption(options) {
        var defaultOption = options[0];
        for (var i = 1; i < options.length; ++i) {
            if (options[i].defaultOption) {
                defaultOption = options[i];
                break;
            }
        }
        return defaultOption;
    }

    function getOptionsByLevel(level) {
        switch (level) {
            case constants.level.ALL_ACCOUNTS:
                return ALL_ACCOUNTS_LEVEL_OPTIONS;
            case constants.level.ACCOUNTS:
                return ACCOUNTS_LEVEL_OPTIONS;
            case constants.level.CAMPAIGNS:
                return CAMPAIGNS_LEVEL_OPTIONS;
            case constants.level.AD_GROUPS:
                return AD_GROUPS_LEVEL_OPTIONS;
        }
    }

    function getOptions(level, breakdown) {
        if (breakdown === constants.breakdown.PUBLISHER)
            throw 'Export by publisher breakdown is not supported';

        var options = angular.copy(getOptionsByLevel(level));
        if (breakdown === constants.breakdown.MEDIA_SOURCE) {
            options[0].name = 'Current View';
        } else {
            options[0].name += ' (totals)';
            options[1].name = 'Current View';
            options[1].defaultOption = true;
        }
        return options;
    }

    return {
        getBaseUrl: getBaseUrl,
        getOptions: getOptions,
        getDefaultOption: getDefaultOption,
    };
});
