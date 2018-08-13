angular
    .module('one.widgets')
    .service('zemGridBulkPublishersActionsService', function(
        zemDataFilterService,
        zemGridBulkPublishersActionsEndpoint,
        zemGridEndpointColumns,
        zemGridConstants,
        zemNavigationNewService,
        zemPermissions
    ) {
        // eslint-disable-line max-len
        this.getBlacklistActions = getBlacklistActions;
        this.getUnlistActions = getUnlistActions;
        this.execute = execute;

        var COLUMNS = zemGridEndpointColumns.COLUMNS;
        var bulkUpdateDefered;

        var BLACKLIST_ADGROUP = {
            name: 'Add to ad group blacklist',
            value: 'blacklist-adgroup',
            entityType: constants.entityType.AD_GROUP,
            configEntityId: 'ad_group',
            level: constants.publisherBlacklistLevel.ADGROUP,
            status: constants.publisherTargetingStatus.BLACKLISTED,
            includeSubdomains: true,
            hasPermission: zemPermissions.hasPermission(
                'zemauth.can_modify_publisher_blacklist_status'
            ),
        };
        var BLACKLIST_CAMPAIGN = {
            name: 'Add to campaign blacklist',
            value: 'blacklist-campaign',
            entityType: constants.entityType.CAMPAIGN,
            configEntityId: 'campaign',
            level: constants.publisherBlacklistLevel.CAMPAIGN,
            status: constants.publisherTargetingStatus.BLACKLISTED,
            includeSubdomains: true,
            hasPermission:
                zemPermissions.hasPermission(
                    'zemauth.can_modify_publisher_blacklist_status'
                ) &&
                zemPermissions.hasPermission(
                    'zemauth.can_access_campaign_account_publisher_blacklist_status'
                ),
        };
        var BLACKLIST_ACCOUNT = {
            name: 'Add to account blacklist',
            value: 'blacklist-account',
            entityType: constants.entityType.ACCOUNT,
            configEntityId: 'account',
            level: constants.publisherBlacklistLevel.ACCOUNT,
            status: constants.publisherTargetingStatus.BLACKLISTED,
            includeSubdomains: true,
            hasPermission:
                zemPermissions.hasPermission(
                    'zemauth.can_modify_publisher_blacklist_status'
                ) &&
                zemPermissions.hasPermission(
                    'zemauth.can_access_campaign_account_publisher_blacklist_status'
                ),
        };
        var BLACKLIST_GLOBAL = {
            name: 'Add to global blacklist',
            value: 'blacklist-global',
            level: constants.publisherBlacklistLevel.GLOBAL,
            status: constants.publisherTargetingStatus.BLACKLISTED,
            includeSubdomains: true,
            internal: zemPermissions.isPermissionInternal(
                'zemauth.can_access_global_publisher_blacklist_status'
            ),
            hasPermission:
                zemPermissions.hasPermission(
                    'zemauth.can_modify_publisher_blacklist_status'
                ) &&
                zemPermissions.hasPermission(
                    'zemauth.can_access_global_publisher_blacklist_status'
                ),
        };

        var UNLIST_ADGROUP = {
            name: 'Remove from ad group blacklist',
            value: 'unlist-adgroup',
            entityType: constants.entityType.AD_GROUP,
            configEntityId: 'ad_group',
            level: constants.publisherBlacklistLevel.ADGROUP,
            status: constants.publisherTargetingStatus.UNLISTED,
            hasPermission: zemPermissions.hasPermission(
                'zemauth.can_modify_publisher_blacklist_status'
            ),
        };
        var UNLIST_CAMPAIGN = {
            name: 'Remove from campaign blacklist',
            value: 'unlist-campaign',
            entityType: constants.entityType.CAMPAIGN,
            configEntityId: 'campaign',
            level: constants.publisherBlacklistLevel.CAMPAIGN,
            status: constants.publisherTargetingStatus.UNLISTED,
            hasPermission:
                zemPermissions.hasPermission(
                    'zemauth.can_modify_publisher_blacklist_status'
                ) &&
                zemPermissions.hasPermission(
                    'zemauth.can_access_campaign_account_publisher_blacklist_status'
                ),
        };
        var UNLIST_ACCOUNT = {
            name: 'Remove from account blacklist',
            value: 'unlist-account',
            entityType: constants.entityType.ACCOUNT,
            configEntityId: 'account',
            level: constants.publisherBlacklistLevel.ACCOUNT,
            status: constants.publisherTargetingStatus.UNLISTED,
            hasPermission:
                zemPermissions.hasPermission(
                    'zemauth.can_modify_publisher_blacklist_status'
                ) &&
                zemPermissions.hasPermission(
                    'zemauth.can_access_campaign_account_publisher_blacklist_status'
                ),
        };
        var UNLIST_GLOBAL = {
            name: 'Remove from global blacklist',
            value: 'unlist-global',
            level: constants.publisherBlacklistLevel.GLOBAL,
            status: constants.publisherTargetingStatus.UNLISTED,
            hasPermission:
                zemPermissions.hasPermission(
                    'zemauth.can_modify_publisher_blacklist_status'
                ) &&
                zemPermissions.hasPermission(
                    'zemauth.can_access_global_publisher_blacklist_status'
                ),
        };

        function getBlacklistActions(level) {
            if (level === constants.level.AD_GROUPS) {
                return [
                    BLACKLIST_ADGROUP,
                    BLACKLIST_CAMPAIGN,
                    BLACKLIST_ACCOUNT,
                    BLACKLIST_GLOBAL,
                ];
            } else if (level === constants.level.CAMPAIGNS) {
                return [
                    BLACKLIST_CAMPAIGN,
                    BLACKLIST_ACCOUNT,
                    BLACKLIST_GLOBAL,
                ];
            } else if (level === constants.level.ACCOUNTS) {
                return [BLACKLIST_ACCOUNT, BLACKLIST_GLOBAL];
            } else if (level === constants.level.ALL_ACCOUNTS) {
                return [BLACKLIST_GLOBAL];
            }
        }

        function getUnlistActions(level) {
            if (level === constants.level.AD_GROUPS) {
                return [
                    UNLIST_ADGROUP,
                    UNLIST_CAMPAIGN,
                    UNLIST_ACCOUNT,
                    UNLIST_GLOBAL,
                ];
            } else if (level === constants.level.CAMPAIGNS) {
                return [UNLIST_CAMPAIGN, UNLIST_ACCOUNT, UNLIST_GLOBAL];
            } else if (level === constants.level.ACCOUNTS) {
                return [UNLIST_ACCOUNT, UNLIST_GLOBAL];
            } else if (level === constants.level.ALL_ACCOUNTS) {
                return [UNLIST_GLOBAL];
            }
        }

        function execute(action, enforceCpc, selection) {
            if (!bulkUpdateDefered) {
                var dateRange = zemDataFilterService.getDateRange();

                var config = {
                    entries: convertRows(
                        selection.selected,
                        action.includeSubdomains
                    ),
                    entries_not_selected: convertRows(selection.unselected),
                    status: action.status,
                    enforce_cpc: enforceCpc,
                    select_all:
                        selection.type ===
                        zemGridConstants.gridSelectionFilterType.ALL,
                    start_date: dateRange.startDate.format('YYYY-MM-DD'),
                    end_date: dateRange.endDate.format('YYYY-MM-DD'),
                };

                if (action.entityType) {
                    config[
                        action.configEntityId
                    ] = zemNavigationNewService.getActiveEntityByType(
                        action.entityType
                    ).id;
                }

                bulkUpdateDefered = zemGridBulkPublishersActionsEndpoint
                    .bulkUpdate(config)
                    .finally(function() {
                        bulkUpdateDefered = null;
                    });
            }
            return bulkUpdateDefered;
        }

        function convertRows(collection, includeSubdomains) {
            return collection
                .filter(function(row) {
                    return row.level === zemGridConstants.gridRowLevel.BASE;
                })
                .map(function(row) {
                    return {
                        source: row.data.stats[COLUMNS.sourceId.field].value,
                        publisher: row.data.stats[COLUMNS.domain.field].value,
                        include_subdomains: includeSubdomains,
                    };
                });
        }
    });
