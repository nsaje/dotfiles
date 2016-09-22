/* globals angular, constants */
'use strict';

angular.module('one.legacy').factory('zemGridBulkActionsService', ['$window', 'api', function ($window, api) {

    function BulkActionsService (grid) {
        this.getActions = getActions;

        function getActions () {
            var level = grid.meta.data.level;
            var breakdown = grid.meta.data.breakdown;
            if (level === constants.level.AD_GROUPS && breakdown === constants.breakdown.CONTENT_AD) {
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
                    hasPermission: grid.meta.api.hasPermission('zemauth.archive_restore_entity'),
                    internal: grid.meta.api.isPermissionInternal('zemauth.archive_restore_entity'),
                    notification: 'All selected Content Ads will be paused and archived.',
                    execute: archive,
                }, {
                    name: 'Restore',
                    value: 'restore',
                    hasPermission: grid.meta.api.hasPermission('zemauth.archive_restore_entity'),
                    internal: grid.meta.api.isPermissionInternal('zemauth.archive_restore_entity'),
                    execute: restore,
                }];
            } else if (level === constants.level.ACCOUNTS && breakdown === constants.breakdown.CAMPAIGN) {
                return [{
                    name: 'Archive',
                    value: 'archive',
                    hasPermission: grid.meta.api.hasPermission('zemauth.archive_restore_entity'),
                    internal: grid.meta.api.isPermissionInternal('zemauth.archive_restore_entity'),
                    checkDisabled: checkCanArchive,
                    notificationDisabled: 'You can not archive active campaigns',
                    execute: nop,
                }, {
                    name: 'Restore',
                    value: 'restore',
                    hasPermission: grid.meta.api.hasPermission('zemauth.archive_restore_entity'),
                    internal: grid.meta.api.isPermissionInternal('zemauth.archive_restore_entity'),
                    execute: nop,
                }];
            } else if (level === constants.level.ALL_ACCOUNTS && breakdown == constants.breakdown.ACCOUNT) {
                return [{
                    name: 'Archive',
                    value: 'archive',
                    hasPermission: grid.meta.api.hasPermission('zemauth.archive_restore_entity'),
                    internal: grid.meta.api.isPermissionInternal('zemauth.archive_restore_entity'),
                    checkDisabled: checkCanArchive,
                    notificationDisabled: 'You can not archive active accounts',
                    execute: nop,
                }, {
                    name: 'Restore',
                    value: 'restore',
                    hasPermission: grid.meta.api.hasPermission('zemauth.archive_restore_entity'),
                    internal: grid.meta.api.isPermissionInternal('zemauth.archive_restore_entity'),
                    execute: nop,
                }];
            } else if (level === constants.level.CAMPAIGNS && breakdown == constants.breakdown.AD_GROUP) {
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
                    hasPermission: grid.meta.api.hasPermission('zemauth.archive_restore_entity'),
                    internal: grid.meta.api.isPermissionInternal('zemauth.archive_restore_entity'),
                    checkDisabled: checkCanArchive,
                    notificationDisabled: 'You can not archive active ad groups',
                    execute: nop,
                }, {
                    name: 'Restore',
                    value: 'restore',
                    hasPermission: grid.meta.api.hasPermission('zemauth.archive_restore_entity'),
                    internal: grid.meta.api.isPermissionInternal('zemauth.archive_restore_entity'),
                    execute: nop,
                }];
            } else if (level === constants.level.AD_GROUPS && breakdown == constants.breakdown.MEDIA_SOURCE) {
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
            var selection = grid.meta.api.getSelection();
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
            url += '&archived=' + !!grid.meta.api.getFilter(grid.meta.api.DS_FILTER.SHOW_ARCHIVED_SOURCES);

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

            grid.meta.api.notify(constants.notificationType.info, msg);
        }

        function refreshData () {
            grid.meta.api.loadData();
            grid.meta.api.clearSelection();
        }
    }

    return {
        createInstance: function (grid) {
            return new BulkActionsService(grid);
        }
    };
}]);
