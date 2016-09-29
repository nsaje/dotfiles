/* globals angular, constants */
'use strict';

angular.module('one.legacy').factory('zemGridBulkActionsService', ['$window', 'api', 'zemGridEndpointColumns', 'zemGridConstants', 'zemAlertsService', function ($window, api, zemGridEndpointColumns, zemGridConstants, zemAlertsService) {

    function BulkActionsService (gridApi) {
        this.getActions = getActions;
        this.setSelectionConfig = setSelectionConfig;

        function setSelectionConfig () {
            var metaData = gridApi.getMetaData();
            if (metaData.level == constants.level.AD_GROUPS && metaData.breakdown === constants.breakdown.CONTENT_AD) {
                initializeContentAdsSelectionConfig();
                gridApi.onMetaDataUpdated(null, initializeContentAdsCustomFilters);
            }
        }

        function initializeContentAdsSelectionConfig () {
            var config = {
                enabled: true,
                filtersEnabled: true,
                levels: [1],
                customFilters: [],
            };
            gridApi.setSelectionOptions(config);
        }

        function initializeContentAdsCustomFilters () {
            var metaData = gridApi.getMetaData();
            if (!metaData || !metaData.ext.batches) return;

            var filters = metaData.ext.batches.map(function (batch) {
                return {
                    name: batch.name,
                    batch: batch, // store for later use
                    callback: function (row) { return row.data.stats[zemGridEndpointColumns.COLUMNS.batchId.field].value === batch.id; },
                };
            });

            var customFilter = {
                type: zemGridConstants.gridSelectionCustomFilterType.LIST,
                name: 'Upload batch',
                filters: filters
            };

            var config = gridApi.getSelectionOptions();
            config.customFilters = [customFilter];
            gridApi.setSelectionOptions(config);
        }

        function getActions () {
            var metaData = gridApi.getMetaData();
            if (metaData.level === constants.level.AD_GROUPS && metaData.breakdown === constants.breakdown.CONTENT_AD) {
                return [{
                    name: 'Pause',
                    value: 'pause',
                    hasPermission: true,
                    execute: pause,
                }, {
                    name: 'Enable',
                    value: 'enable',
                    hasPermission: true,
                    execute: enable,
                }, {
                    name: 'Download',
                    value: 'download',
                    hasPermission: true,
                    execute: download,
                }, {
                    name: 'Archive',
                    value: 'archive',
                    hasPermission: gridApi.hasPermission('zemauth.archive_restore_entity'),
                    internal: gridApi.isPermissionInternal('zemauth.archive_restore_entity'),
                    notification: 'All selected Content Ads will be paused and archived.',
                    execute: archive,
                }, {
                    name: 'Restore',
                    value: 'restore',
                    hasPermission: gridApi.hasPermission('zemauth.archive_restore_entity'),
                    internal: gridApi.isPermissionInternal('zemauth.archive_restore_entity'),
                    execute: restore,
                }];
            } else if (metaData.level === constants.level.ACCOUNTS && metaData.breakdown === constants.breakdown.CAMPAIGN) {
                return [{
                    name: 'Archive',
                    value: 'archive',
                    hasPermission: gridApi.hasPermission('zemauth.archive_restore_entity'),
                    internal: gridApi.isPermissionInternal('zemauth.archive_restore_entity'),
                    checkDisabled: checkCanArchive,
                    notificationDisabled: 'You can not archive active campaigns',
                    execute: nop,
                }, {
                    name: 'Restore',
                    value: 'restore',
                    hasPermission: gridApi.hasPermission('zemauth.archive_restore_entity'),
                    internal: gridApi.isPermissionInternal('zemauth.archive_restore_entity'),
                    execute: nop,
                }];
            } else if (metaData.level === constants.level.ALL_ACCOUNTS && metaData.breakdown == constants.breakdown.ACCOUNT) {
                return [{
                    name: 'Archive',
                    value: 'archive',
                    hasPermission: gridApi.hasPermission('zemauth.archive_restore_entity'),
                    internal: gridApi.isPermissionInternal('zemauth.archive_restore_entity'),
                    checkDisabled: checkCanArchive,
                    notificationDisabled: 'You can not archive active accounts',
                    execute: nop,
                }, {
                    name: 'Restore',
                    value: 'restore',
                    hasPermission: gridApi.hasPermission('zemauth.archive_restore_entity'),
                    internal: gridApi.isPermissionInternal('zemauth.archive_restore_entity'),
                    execute: nop,
                }];
            } else if (metaData.level === constants.level.CAMPAIGNS && metaData.breakdown == constants.breakdown.AD_GROUP) {
                return [{
                    name: 'Pause',
                    value: 'pause',
                    hasPermission: true,
                    execute: nop,
                }, {
                    name: 'Enable',
                    value: 'enable',
                    hasPermission: true,
                    execute: nop,
                }, {
                    name: 'Archive',
                    value: 'archive',
                    hasPermission: gridApi.hasPermission('zemauth.archive_restore_entity'),
                    internal: gridApi.isPermissionInternal('zemauth.archive_restore_entity'),
                    checkDisabled: checkCanArchive,
                    notificationDisabled: 'You can not archive active ad groups',
                    execute: nop,
                }, {
                    name: 'Restore',
                    value: 'restore',
                    hasPermission: gridApi.hasPermission('zemauth.archive_restore_entity'),
                    internal: gridApi.isPermissionInternal('zemauth.archive_restore_entity'),
                    execute: nop,
                }];
            } else if (metaData.level === constants.level.AD_GROUPS && metaData.breakdown == constants.breakdown.MEDIA_SOURCE) {
                return [{
                    name: 'Pause',
                    value: 'pause',
                    hasPermission: true,
                    execute: nop,
                }, {
                    name: 'Enable',
                    value: 'enable',
                    hasPermission: true,
                    execute: nop,
                }];
            }
        }

        function nop () {

        }

        function checkCanArchive () {
            var selection = gridApi.getSelection();
            return !selection.selected.every(function (item) {
                if (item.level != 1) {
                    return true;
                }
                return item.data.stats.status.value !== constants.adGroupSettingsState.ACTIVE;
            });
        }

        function pause (selection) {
            bulkUpdatedState(selection, constants.contentAdSourceState.INACTIVE);
        }

        function enable (selection) {
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
            url += '&archived=' + !!gridApi.getFilter(gridApi.DS_FILTER.SHOW_ARCHIVED_SOURCES);

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

            zemAlertsService.notify(constants.notificationType.warning, msg, true);
        }

        function refreshData () {
            gridApi.loadData();
            gridApi.clearSelection();
        }
    }

    return {
        createInstance: function (gridApi) {
            return new BulkActionsService(gridApi);
        }
    };
}]);
