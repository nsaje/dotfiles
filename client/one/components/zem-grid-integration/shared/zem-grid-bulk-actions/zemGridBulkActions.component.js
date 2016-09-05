/* global angular, constants */
'use strict';

angular.module('one.legacy').directive('zemGridBulkActions', ['$window', 'api', function () {
    return {
        restrict: 'E',
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            api: '=',
        },
        templateUrl: '/components/zem-grid-integration/shared/zem-grid-bulk-actions/zemGridBulkActions.component.html',
        controller: 'zemGridBulkActionsCtrl',
    };
}]);

angular.module('one.legacy').controller('zemGridBulkActionsCtrl', ['$window', 'api', 'zemGridConstants', 'zemGridEndpointColumns', function ($window, api, zemGridConstants, zemGridEndpointColumns) { // eslint-disable-line max-len
    // TODO: alert, update daily stats
    var COLUMNS = zemGridEndpointColumns.COLUMNS;

    var vm = this;

    vm.actions = []; // Defined below
    vm.isEnabled = isEnabled;
    vm.execute = execute;

    initialize();

    function initialize () {
        initializeSelectionConfig();
        vm.api.onMetaDataUpdated(null, initializeCustomFilters);
    }

    function initializeSelectionConfig () {
        var config = {
            enabled: true,
            filtersEnabled: true,
            levels: [1],
            customFilters: [],
        };
        vm.api.setSelectionOptions(config);
    }

    function initializeCustomFilters () {
        var metaData = vm.api.getMetaData();
        if (!metaData || !metaData.ext.batches) return;

        var filters = metaData.ext.batches.map(function (batch) {
            return {
                name: batch.name,
                batch: batch, // store for later use
                callback: function (row) { return row.data.stats[COLUMNS.batchId.field].value === batch.id; },
            };
        });

        var customFilter = {
            type: zemGridConstants.gridSelectionCustomFilterType.LIST,
            name: 'Upload batch',
            filters: filters
        };

        var config = vm.api.getSelectionOptions();
        config.customFilters = [customFilter];
        vm.api.setSelectionOptions(config);
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

        var convertedSelection = {};
        convertedSelection.id = metaData.id;
        convertedSelection.selectedIds = selection.selected.map(function (row) {
            return row.data.stats.id.value;
        });
        convertedSelection.unselectedIds = selection.unselected.map(function (row) {
            return row.data.stats.id.value;
        });
        convertedSelection.filterAll = selection.type === zemGridConstants.gridSelectionFilterType.ALL;
        convertedSelection.filterId = selection.type === zemGridConstants.gridSelectionFilterType.CUSTOM ?
            selection.filter.batch.id : null;

        action.execute(convertedSelection);
    }

    function refreshData () {
        vm.api.loadData();
        vm.api.clearSelection();
    }

    //
    // Actions (TODO: create service when this functionality is expanded)
    //
    vm.actions = [{
        name: 'Pause',
        value: 'pause',
        hasPermission: true,
        execute: pause,
    }, {
        name: 'Resume',
        value: 'resume',
        hasPermission: true,
        execute: resume,
    }, {
        name: 'Download',
        value: 'download',
        hasPermission: true,
        execute: download,
    }, {
        name: 'Archive',
        value: 'archive',
        hasPermission: vm.api.hasPermission('zemauth.archive_restore_entity'),
        internal: vm.api.isPermissionInternal('zemauth.archive_restore_entity'),
        notification: 'All selected Content Ads will be paused and archived.',
        execute: archive,
    }, {
        name: 'Restore',
        value: 'restore',
        hasPermission: vm.api.hasPermission('zemauth.archive_restore_entity'),
        internal: vm.api.isPermissionInternal('zemauth.archive_restore_entity'),
        execute: restore,
    }];

    function getActionByValue (value) {
        return vm.actions.filter(function (action) {
            return action.value === value;
        })[0];
    }

    function pause (selection) {
        bulkUpdatedState(selection, constants.contentAdSourceState.INACTIVE);
    }

    function resume (selection) {
        bulkUpdatedState(selection, constants.contentAdSourceState.ACTIVE);
    }

    function archive (selection) {
        api.adGroupContentAdArchive.archive(
            selection.id,
            selection.selectedIds,
            selection.unselectedIds,
            selection.filterAll,
            selection.filterId).then(function (data) {
                notifyArchivingSuccess(data.data.archived_count, data.data.active_count);
                refreshData();
            });
    }

    function notifyArchivingSuccess (archivedCount, activeCount) {
        // FIXME: find better solution for pluralization
        var msg = archivedCount;
        if (archivedCount === 1) {
            msg += ' Content Ad was archived and it ';
            msg += activeCount === 1 ? 'was' : 'wasn\'t';
        } else {
            msg += ' Content Ad were archived and ';
            if (activeCount === 0) {
                msg += 'none of them were';
            } else {
                msg += activeCount;
                msg += ' of them ';
                msg += activeCount === 1 ? 'was ' : 'were';
            }
        }
        msg += ' active at the time.';

        vm.api.notify(constants.notificationType.info, msg);
    }

    function restore (selection) {
        api.adGroupContentAdArchive.restore(
            selection.id,
            selection.selectedIds,
            selection.unselectedIds,
            selection.filterAll,
            selection.filterId).then(function () {
                refreshData();
            });
    }

    function download (selection) {
        var url = '/api/ad_groups/' + selection.id + '/contentads/csv/?';
        url += 'content_ad_ids_selected=' + selection.selectedIds.join(',');
        url += '&content_ad_ids_not_selected=' + selection.unselectedIds.join(',');
        url += '&archived=' + !!vm.api.getFilter(vm.api.DS_FILTER.SHOW_ARCHIVED_SOURCES);

        if (selection.filterAll) url += '&select_all=' + selection.filterAll;
        if (selection.filterId) url += '&select_batch=' + selection.filterId;

        $window.open(url, '_blank');
    }

    function bulkUpdatedState (selection, state) {
        api.adGroupContentAdState.save(
            selection.id,
            state,
            selection.selectedIds,
            selection.unselectedIds,
            selection.filterAll,
            selection.filterId
        ).then(function () {
            // FIXME: poll updates (editable fields)
            refreshData();
        });
    }
}]);
