angular.module('one.widgets').service('zemGridContainerTabsService', function (zemPermissions) { // eslint-disable-line

    var TABS = {
        accounts: {
            name: 'Accounts',
            breakdown: constants.breakdown.ACCOUNT,
        },
        campaigns: {
            name: 'Campaigns',
            breakdown: constants.breakdown.CAMPAIGN,
        },
        ad_groups: {
            name: 'Ad groups',
            breakdown: constants.breakdown.AD_GROUP,
        },
        content_ads: {
            name: 'Content Ads',
            breakdown: constants.breakdown.CONTENT_AD,
        },
        sources: {
            name: 'Media Sources',
            breakdown: constants.breakdown.MEDIA_SOURCE,
        },
        publishers: {
            name: 'Publishers',
            breakdown: constants.breakdown.PUBLISHER,
        },
        insights: {
            name: 'Content Insights',
            breakdown: 'insights',
        },
    };

    this.createTabOptions = createTabOptions;

    //
    // Public methods
    //
    function createTabOptions (entity) {
        var options = [];
        if (!entity) {
            options = [
                TABS.accounts,
                TABS.sources,
            ];
            if (zemPermissions.hasPermission('zemauth.can_see_publishers_all_levels')) {
                options.push(TABS.publishers);
            }
        } else if (entity.type === constants.entityType.ACCOUNT) {
            options = [
                TABS.campaigns,
                TABS.sources,
            ];
            if (zemPermissions.hasPermission('zemauth.can_see_publishers_all_levels')) {
                options.push(TABS.publishers);
            }
        } else if (entity && entity.type === constants.entityType.CAMPAIGN) {
            options = [
                TABS.ad_groups,
                TABS.sources,
                TABS.insights,
            ];
            if (zemPermissions.hasPermission('zemauth.can_see_publishers_all_levels')) {
                options.splice(2, 0, TABS.publishers);
            }
        } else if (entity && entity.type === constants.entityType.AD_GROUP) {
            options = [
                TABS.content_ads,
                TABS.sources,
                TABS.publishers,
            ];
        }
        return options;
    }
});
