/* global angular, constants */

angular.module('one.widgets').component('zemGridBulkPublishersActions', {
    bindings: {
        api: '=',
    },
    templateUrl: '/app/widgets/zem-grid-integration/shared/bulk-publishers-actions/zemGridBulkPublishersActions.component.html', // eslint-disable-line max-len
    controller: function ($scope, $window, zemGridConstants, zemGridBulkPublishersActionsService, zemAlertsService) { // eslint-disable-line max-len
        var MAX_BLACKLISTED_PUBLISHERS_YAHOO = 0;
        var MSG_GLOBAL_UPDATE_ALERT = 'This action will affect all accounts. Are you sure you want to proceed?';
        var MSG_DISABLED_ROW = '' +
            'This publisher can\'t be blacklisted because the media source ' +
            'doesn\'t support publisher blacklisting or the limit of max ' +
            'blacklisted publisher on this particular media source has been reached.\n' +
            'Contact your account manager for further details.';

        var $ctrl = this;

        $ctrl.blacklistActions = []; // Defined in $onInit
        $ctrl.unlistActions = []; // Defined in $onInit
        $ctrl.isEnabled = isEnabled;
        $ctrl.execute = execute;

        var actions;

        $ctrl.$onInit = function () {
            $ctrl.service = zemGridBulkPublishersActionsService.createInstance($ctrl.api);
            initializeActions();
            initializeSelectionConfig();
            $ctrl.api.onSelectionUpdated($scope, updateActionStates);
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

        function initializeActions () {
            $ctrl.blacklistActions = $ctrl.service.getBlacklistActions();
            $ctrl.unlistActions = $ctrl.service.getUnlistActions();

            actions = $ctrl.blacklistActions.concat($ctrl.unlistActions).reduce(function (o, action) {
                o[action.value] = action;
                return o;
            }, {});
        }

        function updateActionStates () {
            var supportedLevels = getSupportedLevels();
            angular.forEach(actions, function (action) {
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
                var exchangeData = selectedRows[i].data.stats.exchange;
                if (exchangeData && exchange === exchangeData.value) {
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
            var action = actions[actionValue];

            if (action.level === constants.publisherBlacklistLevel.GLOBAL) {
                if (!confirm(MSG_GLOBAL_UPDATE_ALERT)) {
                    return;
                }
            }

            $ctrl.service
                .execute(action, false)
                .then(function () {
                    refreshData();
                    $ctrl.api.clearSelection();
                })
                .catch(function (err) {
                    if (!err.data.errors || !err.data.errors.cpc_constraints) { return; }
                    if (!confirm('If you want to blacklist more than 30 Outbrain publishers, Outbrain bid CPC will be automatically set to at least $0.65 in all ad groups within this account. Are you sure you want to proceed with blaklisting?')) { // eslint-disable-line max-len
                        return;
                    }
                    $ctrl.service.execute(action, true).then(refreshData).catch(function (err) {
                        if (!err.data.errors || !err.data.errors.cpc_constraints) { return; }
                        zemAlertsService.notify(constants.notificationType.warning, err.data.errors.cpc_constraints[0], true); // eslint-disable-line max-len
                    });
                });
        }

        function refreshData () {
            $ctrl.api.loadData();
            $ctrl.api.clearSelection();
        }
    }
});
