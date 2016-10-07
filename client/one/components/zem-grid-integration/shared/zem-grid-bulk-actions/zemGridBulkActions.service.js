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

        var ACTIONS = {
            pause: {
                name: 'Pause',
                value: 'pause',
                hasPermission: true,
                execute: pause,
            },
            enable: {
                name: 'Enable',
                value: 'enable',
                hasPermission: true,
                execute: enable,
            },
            download: {
                name: 'Download',
                value: 'download',
                hasPermission: true,
                execute: download,
            },
            restore: {
                name: 'Restore',
                value: 'restore',
                hasPermission: gridApi.hasPermission('zemauth.archive_restore_entity'),
                internal: gridApi.isPermissionInternal('zemauth.archive_restore_entity'),
                execute: restore,
            },
        };

        function getActions () {
            var metaData = gridApi.getMetaData();
            if (metaData.level === constants.level.AD_GROUPS && metaData.breakdown === constants.breakdown.CONTENT_AD) {
                return [
                    ACTIONS.pause,
                    ACTIONS.enable,
                    ACTIONS.download,
                    {
                        name: 'Archive',
                        value: 'archive',
                        hasPermission: gridApi.hasPermission('zemauth.archive_restore_entity'),
                        internal: gridApi.isPermissionInternal('zemauth.archive_restore_entity'),
                        notification: 'All selected Content Ads will be paused and archived.',
                        execute: archive,
                    },
                    ACTIONS.restore
                ];
            } else if (metaData.level === constants.level.ACCOUNTS && metaData.breakdown === constants.breakdown.CAMPAIGN) {
                return [
                    {
                        name: 'Archive',
                        value: 'archive',
                        hasPermission: gridApi.hasPermission('zemauth.archive_restore_entity'),
                        internal: gridApi.isPermissionInternal('zemauth.archive_restore_entity'),
                        checkDisabled: checkCanArchive,
                        notificationDisabled: 'You can not archive active campaigns',
                        execute: archive,
                    },
                    ACTIONS.restore
                ];
            } else if (metaData.level === constants.level.ALL_ACCOUNTS && metaData.breakdown == constants.breakdown.ACCOUNT) {
                return [
                    {
                        name: 'Archive',
                        value: 'archive',
                        hasPermission: gridApi.hasPermission('zemauth.archive_restore_entity'),
                        internal: gridApi.isPermissionInternal('zemauth.archive_restore_entity'),
                        checkDisabled: checkCanArchive,
                        notificationDisabled: 'You can not archive active accounts',
                        execute: archive,
                    },
                    ACTIONS.restore
                ];
            } else if (metaData.level === constants.level.CAMPAIGNS && metaData.breakdown == constants.breakdown.AD_GROUP) {
                return [
                    ACTIONS.pause,
                    ACTIONS.enable,
                    {
                        name: 'Archive',
                        value: 'archive',
                        hasPermission: gridApi.hasPermission('zemauth.archive_restore_entity'),
                        internal: gridApi.isPermissionInternal('zemauth.archive_restore_entity'),
                        checkDisabled: checkCanArchive,
                        notificationDisabled: 'You can not archive active ad groups',
                        execute: archive,
                    },
                    ACTIONS.restore,
                ];
            } else if (metaData.level === constants.level.AD_GROUPS && metaData.breakdown == constants.breakdown.MEDIA_SOURCE) {
                return [
                    ACTIONS.pause,
                    ACTIONS.enable
                ];
            }
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
            var metaData = gridApi.getMetaData();
            api.bulkActions.archive(
                metaData.level,
                metaData.breakdown,
                metaData.id,
                selection
            ).then(function (data) {
                if (metaData.level == constants.level.AD_GROUPS) {
                    notifyArchivingSuccess(data.data.archived_count, data.data.active_count);
                }
                refreshData();
            }, handleError);
        }

        function restore (selection) {
            var metaData = gridApi.getMetaData();
            api.bulkActions.restore(
                metaData.level,
                metaData.breakdown,
                metaData.id,
                selection
            ).then(function () {
                refreshData();
            }, handleError);
        }

        function download (selection) {
            var metaData = gridApi.getMetaData();
            var url = '/api/ad_groups/' + metaData.id + '/contentads/csv/?';
            url += 'content_ad_ids_selected=' + selection.selectedIds.join(',');
            url += '&content_ad_ids_not_selected=' + selection.unselectedIds.join(',');
            url += '&archived=' + !!gridApi.getFilter(gridApi.DS_FILTER.SHOW_ARCHIVED_SOURCES);

            if (selection.filterAll) url += '&select_all=' + selection.filterAll;
            if (selection.filterId) url += '&select_batch=' + selection.filterId;

            $window.open(url, '_blank');
        }

        function bulkUpdatedState (selection, state) {
            var metaData = gridApi.getMetaData();
            api.bulkActions.state(
                metaData.level,
                metaData.breakdown,
                metaData.id,
                selection,
                state
            ).then(function () {
                // FIXME: poll updates (editable fields)
                refreshData();
            }, handleError);
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

        function handleError (data) {
            zemAlertsService.notify(constants.notificationType.danger, 'Error executing action: ' + data.data.message, true);
        }
    }

    return {
        createInstance: function (gridApi) {
            return new BulkActionsService(gridApi);
        }
    };
}]);
