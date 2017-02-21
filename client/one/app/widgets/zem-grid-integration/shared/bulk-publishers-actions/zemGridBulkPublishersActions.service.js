/* globals angular, constants */
'use strict';

angular.module('one.widgets').factory('zemGridBulkPublishersActionsService', function ($q, zemDataFilterService, zemGridBulkPublishersActionsEndpoint, zemGridEndpointColumns, zemGridConstants) { // eslint-disable-line max-len
    function BulkActionsService (gridApi) {
        this.getBlacklistActions = getBlacklistActions;
        this.getUnlistActions = getUnlistActions;
        this.execute = execute;

        var COLUMNS = zemGridEndpointColumns.COLUMNS;
        var bulkUpdateDefered;

        function getBlacklistActions () {
            return [{
                name: 'Blacklist in this adgroup',
                value: 'blacklist-adgroup',
                level: constants.publisherBlacklistLevel.ADGROUP,
                status: constants.publisherTargetingStatus.BLACKLISTED,
                includeSubdomains: true,
                hasPermission: gridApi.hasPermission('zemauth.can_modify_publisher_blacklist_status'),
            }, {
                name: 'Blacklist in this campaign',
                value: 'blacklist-campaign',
                level: constants.publisherBlacklistLevel.CAMPAIGN,
                status: constants.publisherTargetingStatus.BLACKLISTED,
                includeSubdomains: true,
                hasPermission: gridApi.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
                    gridApi.hasPermission('zemauth.can_access_campaign_account_publisher_blacklist_status')
            }, {
                name: 'Blacklist in this account',
                value: 'blacklist-account',
                level: constants.publisherBlacklistLevel.ACCOUNT,
                status: constants.publisherTargetingStatus.BLACKLISTED,
                includeSubdomains: true,
                hasPermission: gridApi.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
                    gridApi.hasPermission('zemauth.can_access_campaign_account_publisher_blacklist_status')
            }, {
                name: 'Blacklist globally on RTB sources',
                value: 'blacklist-global',
                level: constants.publisherBlacklistLevel.GLOBAL,
                status: constants.publisherTargetingStatus.BLACKLISTED,
                includeSubdomains: true,
                internal: gridApi.isPermissionInternal('zemauth.can_access_global_publisher_blacklist_status'),
                hasPermission: gridApi.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
                    gridApi.hasPermission('zemauth.can_access_global_publisher_blacklist_status')
            }];
        }

        function getUnlistActions () {
            return [{
                name: 'Re-enable in this adgroup',
                value: 'unlist-adgroup',
                level: constants.publisherBlacklistLevel.ADGROUP,
                status: constants.publisherTargetingStatus.UNLISTED,
                hasPermission: gridApi.hasPermission('zemauth.can_modify_publisher_blacklist_status')
            }, {
                name: 'Re-enable in this campaign',
                value: 'unlist-campaign',
                level: constants.publisherBlacklistLevel.CAMPAIGN,
                status: constants.publisherTargetingStatus.UNLISTED,
                hasPermission: gridApi.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
                    gridApi.hasPermission('zemauth.can_access_campaign_account_publisher_blacklist_status')
            }, {
                name: 'Re-enable in this account',
                value: 'unlist-account',
                level: constants.publisherBlacklistLevel.ACCOUNT,
                status: constants.publisherTargetingStatus.UNLISTED,
                hasPermission: gridApi.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
                    gridApi.hasPermission('zemauth.can_access_campaign_account_publisher_blacklist_status')
            }, {
                name: 'Re-enable globally on RTB sources',
                value: 'unlist-global',
                level: constants.publisherBlacklistLevel.GLOBAL,
                status: constants.publisherTargetingStatus.UNLISTED,
                hasPermission: gridApi.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
                    gridApi.hasPermission('zemauth.can_access_global_publisher_blacklist_status')
            }];
        }

        function execute (action, enforceCpc) {
            if (!bulkUpdateDefered) {
                var meta = gridApi.getMetaData();
                var selection = gridApi.getSelection();
                var dateRange = zemDataFilterService.getDateRange();

                var config = {
                    entries: convertRows(selection.selected, action.includeSubdomains),
                    entries_not_selected: convertRows(selection.unselected),
                    status: action.status,
                    ad_group: meta.id,
                    level: action.level,
                    enforce_cpc: enforceCpc,
                    select_all: selection.type === zemGridConstants.gridSelectionFilterType.ALL,
                    start_date: dateRange.startDate.format('YYYY-MM-DD'),
                    end_date: dateRange.endDate.format('YYYY-MM-DD')
                };

                bulkUpdateDefered = zemGridBulkPublishersActionsEndpoint.bulkUpdate(config).finally(function () {
                    bulkUpdateDefered = null;
                });
            }
            return bulkUpdateDefered;
        }

        function convertRows (collection, includeSubdomains) {
            return collection.filter(function (row) {
                return row.level === zemGridConstants.gridRowLevel.BASE;
            }).map(function (row) {
                return {
                    source: row.data.stats[COLUMNS.sourceId.field].value,
                    publisher: row.data.stats[COLUMNS.domain.field].value,
                    include_subdomains: includeSubdomains,
                };
            });
        }
    }

    return {
        createInstance: function (gridApi) {
            return new BulkActionsService(gridApi);
        }
    };
});