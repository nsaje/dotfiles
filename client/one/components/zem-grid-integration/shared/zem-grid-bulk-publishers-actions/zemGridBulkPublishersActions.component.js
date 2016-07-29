/* global oneApp, constants */
'use strict';

oneApp.directive('zemGridBulkPublishersActions', ['$window', 'api', function () {
    return {
        restrict: 'E',
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            api: '=',
        },
        templateUrl: '/components/zem-grid-integration/shared/zem-grid-bulk-publishers-actions/zemGridBulkPublishersActions.component.html',
        controller: 'zemGridBulkPublishersActionsCtrl',
    };
}]);

oneApp.controller('zemGridBulkPublishersActionsCtrl', ['$window', 'api', 'zemGridConstants', 'zemGridEndpointColumns', function ($window, api, zemGridConstants, zemGridEndpointColumns) { // eslint-disable-line max-len
    var COLUMNS = zemGridEndpointColumns.COLUMNS;
    var MAX_BLACKLISTED_PUBLISHERS_OUTBRAIN = 10;
    var MAX_BLACKLISTED_PUBLISHERS_YAHOO = 0;

    var MSG_GLOBAL_UPDATE_ALERT = 'This action will affect all accounts. Are you sure you want to proceed?';
    var MSG_DISABLED_ROW = '' +
        'This publisher can\'t be blacklisted because the media source ' +
        'doesn\'t support publisher blacklisting or the limit of max ' +
        'blacklisted publisher on this particular media source has been reached.\n' +
        'Contact your account manager for further details.';

    var vm = this;

    vm.publisherBlacklistActions = []; // Defined below
    vm.publisherEnableActions = []; // Defined below
    vm.isEnabled = isEnabled;
    vm.execute = execute;

    initialize();

    function initialize () {
        initializeSelectionConfig();
        vm.api.onSelectionUpdated(null, updateActionStates);
    }

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
                    var exchange = row.data.stats.exchange.value;
                    var sum = getBlacklistedPublishers(exchange) + getSelectedPublishers(exchange);
                    return sum < getMaxBlacklistedPublishers(exchange);
                },
            }
        };
        vm.api.setSelectionOptions(config);
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
        if (vm.api.getSelection().type === zemGridConstants.gridSelectionFilterType.ALL) {
            return true;
        }

        return getSelectedPublishers(constants.sourceTypeName.OUTBRAIN) > 0;
    }

    function getSelectedPublishers (exchange) {
        var selectedRows = vm.api.getSelection().selected;
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
            return vm.api.getMetaData().ext.obBlacklistedCount || 0;
        default:
            return 0; // Unknown
        }
    }

    function getMaxBlacklistedPublishers (exchange) {
        switch (exchange) {
        case constants.sourceTypeName.OUTBRAIN:
            return MAX_BLACKLISTED_PUBLISHERS_OUTBRAIN;
        case constants.sourceTypeName.YAHOO:
            return MAX_BLACKLISTED_PUBLISHERS_YAHOO;
        default:
            return Number.MAX_VALUE;
        }
    }

    function isEnabled () {
        var selection = vm.api.getSelection();
        if (selection.type === zemGridConstants.gridSelectionFilterType.NONE) {
            return selection.selected.length > 0;
        }
        return true;
    }

    function execute (actionValue) {
        var metaData = vm.api.getMetaData();
        var selection = vm.api.getSelection();
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

        action.execute(convertedSelection);
    }

    function convertRows (collection) {
        return collection.map(function (row) {
            return {
                source_id: row.data.stats[COLUMNS.sourceId.field].value,
                domain: row.data.stats[COLUMNS.domain.field].value,
                exchange: row.data.stats[COLUMNS.exchange.field].value,
                external_id: row.data.stats[COLUMNS.externalId.field].value,
            };
        });
    }

    //
    // Actions (TODO: create service when this functionallity is expanded)
    //
    vm.publisherBlacklistActions = [{
        name: 'Blacklist in this adgroup',
        value: 'blacklist-adgroup',
        level: constants.publisherBlacklistLevel.ADGROUP,
        state: constants.publisherStatus.BLACKLISTED,
        hasPermission: vm.api.hasPermission('zemauth.can_modify_publisher_blacklist_status')
    }, {
        name: 'Blacklist in this campaign',
        value: 'blacklist-campaign',
        level: constants.publisherBlacklistLevel.CAMPAIGN,
        state: constants.publisherStatus.BLACKLISTED,
        hasPermission: vm.api.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
        vm.api.hasPermission('zemauth.can_access_campaign_account_publisher_blacklist_status')
    }, {
        name: 'Blacklist in this account',
        value: 'blacklist-account',
        level: constants.publisherBlacklistLevel.ACCOUNT,
        state: constants.publisherStatus.BLACKLISTED,
        hasPermission: vm.api.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
        vm.api.hasPermission('zemauth.can_access_campaign_account_publisher_blacklist_status')
    }, {
        name: 'Blacklist globally',
        value: 'blacklist-global',
        level: constants.publisherBlacklistLevel.GLOBAL,
        state: constants.publisherStatus.BLACKLISTED,
        hasPermission: vm.api.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
        vm.api.hasPermission('zemauth.can_access_global_publisher_blacklist_status')
    }];

    vm.publisherEnableActions = [{
        name: 'Re-enable in this adgroup',
        value: 'enable-adgroup',
        level: constants.publisherBlacklistLevel.ADGROUP,
        state: constants.publisherStatus.ENABLED,
        hasPermission: vm.api.hasPermission('zemauth.can_modify_publisher_blacklist_status')
    }, {
        name: 'Re-enable in this campaign',
        value: 'enable-campaign',
        level: constants.publisherBlacklistLevel.CAMPAIGN,
        state: constants.publisherStatus.ENABLED,
        hasPermission: vm.api.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
        vm.api.hasPermission('zemauth.can_access_campaign_account_publisher_blacklist_status')
    }, {
        name: 'Re-enable in this account',
        value: 'enable-account',
        level: constants.publisherBlacklistLevel.ACCOUNT,
        state: constants.publisherStatus.ENABLED,
        hasPermission: vm.api.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
        vm.api.hasPermission('zemauth.can_access_campaign_account_publisher_blacklist_status')
    }, {
        name: 'Re-enable globally',
        value: 'enable-global',
        level: constants.publisherBlacklistLevel.GLOBAL,
        state: constants.publisherStatus.ENABLED,
        hasPermission: vm.api.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
        vm.api.hasPermission('zemauth.can_access_global_publisher_blacklist_status')
    }];

    var actions = vm.publisherBlacklistActions.concat(vm.publisherEnableActions);

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
        api.adGroupPublishersState.save(
            selection.id,
            state,
            level,
            vm.api.getDateRange().startDate,
            vm.api.getDateRange().endDate,
            selection.selectedPublishers,
            selection.unselectedPublishers,
            selection.filterAll
        ).then(function () {
            vm.api.loadData();
        });
    }
}]);
