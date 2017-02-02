/* global angular, constants */

angular.module('one.widgets').component('zemGridBulkPublishersActions', {
    bindings: {
        api: '=',
    },
    templateUrl: '/app/widgets/zem-grid-integration/shared/bulk-publishers-actions/zemGridBulkPublishersActions.component.html', // eslint-disable-line max-len
    controller: function ($window, api, zemGridConstants, zemGridEndpointColumns, zemDataFilterService) { // eslint-disable-line max-len
        var COLUMNS = zemGridEndpointColumns.COLUMNS;
        var MAX_BLACKLISTED_PUBLISHERS_YAHOO = 0;

        var MSG_GLOBAL_UPDATE_ALERT = 'This action will affect all accounts. Are you sure you want to proceed?';
        var MSG_DISABLED_ROW = '' +
            'This publisher can\'t be blacklisted because the media source ' +
            'doesn\'t support publisher blacklisting or the limit of max ' +
            'blacklisted publisher on this particular media source has been reached.\n' +
            'Contact your account manager for further details.';

        var $ctrl = this;

        $ctrl.publisherBlacklistActions = []; // Defined below
        $ctrl.publisherEnableActions = []; // Defined below
        $ctrl.isEnabled = isEnabled;
        $ctrl.execute = execute;

        $ctrl.$onInit = function () {
            initializeSelectionConfig();
            $ctrl.api.onSelectionUpdated(null, updateActionStates);
        };

        function initializeSelectionConfig () {
            var config = {
                enabled: true,
                filtersEnabled: true,
                levels: [1],
                info: {
                    disabledRow: MSG_DISABLED_ROW,
                },
                callbacks: {
                    isRowSelectable: function (row) {
                        if (!row.data.stats.exchange) return false;
                        var exchange = row.data.stats.exchange.value;
                        var sum = getBlacklistedPublishers(exchange) + getSelectedPublishers(exchange);
                        return sum < getMaxBlacklistedPublishers(exchange);
                    },
                }
            };
            $ctrl.api.setSelectionOptions(config);
        }

        function updateActionStates () {
            var supportedLevels = getSupportedLevels();
            actions.forEach(function (action) {
                action.disabled = supportedLevels.indexOf(action.level) < 0;
            });
        }

        function getSupportedLevels () {
            if (isOutbrainPublisherSelected()) {
                return [constants.publisherBlacklistLevel.ACCOUNT];
            }

            return [constants.publisherBlacklistLevel.GLOBAL,
                constants.publisherBlacklistLevel.ACCOUNT,
                constants.publisherBlacklistLevel.CAMPAIGN,
                constants.publisherBlacklistLevel.ADGROUP];
        }

        function isOutbrainPublisherSelected () {
            if ($ctrl.api.getSelection().type === zemGridConstants.gridSelectionFilterType.ALL) {
                return true;
            }

            return getSelectedPublishers(constants.sourceTypeName.OUTBRAIN) > 0;
        }

        function getSelectedPublishers (exchange) {
            var selectedRows = $ctrl.api.getSelection().selected;
            var count = 0;
            for (var i = 0; i < selectedRows.length; i++) {
                if (exchange === selectedRows[i].data.stats.exchange.value) {
                    count++;
                }
            }
            return count;
        }

        function getBlacklistedPublishers (exchange) {
            switch (exchange) {
            case constants.sourceTypeName.OUTBRAIN:
                return $ctrl.api.getMetaData().ext.obBlacklistedCount || 0;
            default:
                return 0; // Unknown
            }
        }

        function getMaxBlacklistedPublishers (exchange) {
            switch (exchange) {
            case constants.sourceTypeName.YAHOO:
                return MAX_BLACKLISTED_PUBLISHERS_YAHOO;
            default:
                return Number.MAX_VALUE;
            }
        }

        function isEnabled () {
            var selection = $ctrl.api.getSelection();
            if (selection.type === zemGridConstants.gridSelectionFilterType.NONE) {
                return selection.selected.length > 0;
            }
            return true;
        }

        function execute (actionValue) {
            var metaData = $ctrl.api.getMetaData();
            var selection = $ctrl.api.getSelection();
            var action = getActionByValue(actionValue);

            if (action.level === constants.publisherBlacklistLevel.GLOBAL) {
                if (!confirm(MSG_GLOBAL_UPDATE_ALERT)) {
                    return;
                }
            }

            var convertedSelection = {};
            convertedSelection.id = metaData.id;
            convertedSelection.selectedPublishers = convertRows(selection.selected);
            convertedSelection.unselectedPublishers = convertRows(selection.unselected);
            convertedSelection.filterAll = selection.type === zemGridConstants.gridSelectionFilterType.ALL;

            $ctrl.api.clearSelection();
            action.execute(convertedSelection);
        }

        function convertRows (collection) {
            return collection.filter(function (row) {
                return row.level === zemGridConstants.gridRowLevel.BASE;
            }).map(function (row) {
                return {
                    source_id: row.data.stats[COLUMNS.sourceId.field].value,
                    domain: row.data.stats[COLUMNS.domain.field].value,
                    exchange: row.data.stats[COLUMNS.exchange.field].value,
                    external_id: row.data.stats[COLUMNS.externalId.field].value,
                };
            });
        }

        function refreshData () {
            $ctrl.api.loadData();
            $ctrl.api.clearSelection();
        }

        //
        // Actions (TODO: create service when this functionallity is expanded)
        //
        $ctrl.publisherBlacklistActions = [{
            name: 'Blacklist in this adgroup',
            value: 'blacklist-adgroup',
            level: constants.publisherBlacklistLevel.ADGROUP,
            state: constants.publisherStatus.BLACKLISTED,
            hasPermission: $ctrl.api.hasPermission('zemauth.can_modify_publisher_blacklist_status')
        }, {
            name: 'Blacklist in this campaign',
            value: 'blacklist-campaign',
            level: constants.publisherBlacklistLevel.CAMPAIGN,
            state: constants.publisherStatus.BLACKLISTED,
            hasPermission: $ctrl.api.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
            $ctrl.api.hasPermission('zemauth.can_access_campaign_account_publisher_blacklist_status')
        }, {
            name: 'Blacklist in this account',
            value: 'blacklist-account',
            level: constants.publisherBlacklistLevel.ACCOUNT,
            state: constants.publisherStatus.BLACKLISTED,
            hasPermission: $ctrl.api.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
            $ctrl.api.hasPermission('zemauth.can_access_campaign_account_publisher_blacklist_status')
        }, {
            name: 'Blacklist globally on RTB sources',
            value: 'blacklist-global',
            internal: $ctrl.api.isPermissionInternal('zemauth.can_access_global_publisher_blacklist_status'),
            level: constants.publisherBlacklistLevel.GLOBAL,
            state: constants.publisherStatus.BLACKLISTED,
            hasPermission: $ctrl.api.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
            $ctrl.api.hasPermission('zemauth.can_access_global_publisher_blacklist_status')
        }];

        $ctrl.publisherEnableActions = [{
            name: 'Re-enable in this adgroup',
            value: 'enable-adgroup',
            level: constants.publisherBlacklistLevel.ADGROUP,
            state: constants.publisherStatus.ENABLED,
            hasPermission: $ctrl.api.hasPermission('zemauth.can_modify_publisher_blacklist_status')
        }, {
            name: 'Re-enable in this campaign',
            value: 'enable-campaign',
            level: constants.publisherBlacklistLevel.CAMPAIGN,
            state: constants.publisherStatus.ENABLED,
            hasPermission: $ctrl.api.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
            $ctrl.api.hasPermission('zemauth.can_access_campaign_account_publisher_blacklist_status')
        }, {
            name: 'Re-enable in this account',
            value: 'enable-account',
            level: constants.publisherBlacklistLevel.ACCOUNT,
            state: constants.publisherStatus.ENABLED,
            hasPermission: $ctrl.api.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
            $ctrl.api.hasPermission('zemauth.can_access_campaign_account_publisher_blacklist_status')
        }, {
            name: 'Re-enable globally on RTB sources',
            value: 'enable-global',
            level: constants.publisherBlacklistLevel.GLOBAL,
            state: constants.publisherStatus.ENABLED,
            hasPermission: $ctrl.api.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
            $ctrl.api.hasPermission('zemauth.can_access_global_publisher_blacklist_status')
        }];

        var actions = $ctrl.publisherBlacklistActions.concat($ctrl.publisherEnableActions);

        // Create actions' execute functions
        actions.forEach(function (action) {
            action.execute = function (selection) {
                bulkUpdatePublishers(selection, action.state, action.level);
            };
        });

        function getActionByValue (value) {
            return actions.filter(function (action) {
                return action.value === value;
            })[0];
        }

        function bulkUpdatePublishers (selection, state, level) {
            var dateRange = zemDataFilterService.getDateRange(),
                savePublisherState = function (enforceCpc) {
                    return api.adGroupPublishersState.save(
                        selection.id,
                        state,
                        level,
                        dateRange.startDate,
                        dateRange.endDate,
                        selection.selectedPublishers,
                        selection.unselectedPublishers,
                        selection.filterAll,
                        enforceCpc
                    );
                },
                trySaveWithEnforcedCpc = function (err) {
                    if (!err.data.errors || !err.data.errors.cpc_constraints) { return; }
                    if (!confirm('If you want to blacklist more than 30 Outbrain publishers, Outbrain bid CPC will be automatically set to at least $0.65 in all ad groups within this account. Are you sure you want to proceed with blaklisting?')) { // eslint-disable-line max-len
                        return;
                    }
                    savePublisherState(true).then(refreshData);
                };
            savePublisherState(false).then(refreshData).catch(trySaveWithEnforcedCpc);
        }
    }
});
