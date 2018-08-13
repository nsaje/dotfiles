angular
    .module('one.widgets')
    .service('zemGridContainerTabsService', function(zemPermissions) {
        // eslint-disable-line

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
        function createTabOptions(entity) {
            var options = [];
            if (!entity) {
                options = [
                    angular.copy(TABS.accounts),
                    angular.copy(TABS.sources),
                ];
                if (
                    zemPermissions.hasPermission(
                        'zemauth.can_see_publishers_all_levels'
                    )
                ) {
                    options.push(angular.copy(TABS.publishers));
                }
            } else if (entity.type === constants.entityType.ACCOUNT) {
                options = [
                    angular.copy(TABS.campaigns),
                    angular.copy(TABS.sources),
                ];
                if (
                    zemPermissions.hasPermission(
                        'zemauth.can_see_publishers_all_levels'
                    )
                ) {
                    options.push(angular.copy(TABS.publishers));
                }
            } else if (
                entity &&
                entity.type === constants.entityType.CAMPAIGN
            ) {
                options = [
                    angular.copy(TABS.ad_groups),
                    angular.copy(TABS.sources),
                    angular.copy(TABS.insights),
                ];
                if (
                    zemPermissions.hasPermission(
                        'zemauth.can_see_publishers_all_levels'
                    )
                ) {
                    options.splice(2, 0, angular.copy(TABS.publishers));
                }
            } else if (
                entity &&
                entity.type === constants.entityType.AD_GROUP
            ) {
                options = [
                    angular.copy(TABS.content_ads),
                    angular.copy(TABS.sources),
                    angular.copy(TABS.publishers),
                ];
            }
            return options;
        }
    });
