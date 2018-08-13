angular
    .module('one.widgets')
    .factory('zemGridBulkActionsService', function(
        $q,
        $window,
        zemEntityService,
        zemGridEndpointColumns,
        zemGridConstants,
        zemAlertsService,
        zemUploadService,
        zemUploadApiConverter,
        zemCloneContentService
    ) {
        // eslint-disable-line max-len

        function BulkActionsService(gridApi) {
            this.getActions = getActions;
            this.setSelectionConfig = setSelectionConfig;

            function setSelectionConfig() {
                var metaData = gridApi.getMetaData();
                if (
                    metaData.level === constants.level.AD_GROUPS &&
                    metaData.breakdown === constants.breakdown.CONTENT_AD
                ) {
                    initializeContentAdsSelectionConfig();
                    gridApi.onMetaDataUpdated(
                        null,
                        initializeContentAdsCustomFilters
                    );
                }
            }

            function initializeContentAdsSelectionConfig() {
                var config = {
                    enabled: true,
                    filtersEnabled: true,
                    levels: [1],
                    customFilters: [],
                };
                gridApi.setSelectionOptions(config);
            }

            function initializeContentAdsCustomFilters() {
                var metaData = gridApi.getMetaData();
                if (!metaData || !metaData.ext.batches) return;

                var filters = metaData.ext.batches.map(function(batch) {
                    return {
                        name: batch.name,
                        batch: batch, // store for later use
                        callback: function(row) {
                            return (
                                row.data.stats[
                                    zemGridEndpointColumns.COLUMNS.batchId.field
                                ].value === batch.id
                            );
                        },
                    };
                });

                var customFilter = {
                    type: zemGridConstants.gridSelectionCustomFilterType.LIST,
                    name: 'Upload batch',
                    filters: filters,
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
                    hasPermission: gridApi.hasPermission(
                        'zemauth.archive_restore_entity'
                    ),
                    internal: gridApi.isPermissionInternal(
                        'zemauth.archive_restore_entity'
                    ),
                    execute: restore,
                },
                edit: {
                    name: 'Edit',
                    value: 'edit',
                    hasPermission: gridApi.hasPermission(
                        'zemauth.can_edit_content_ads'
                    ),
                    internal: gridApi.isPermissionInternal(
                        'zemauth.can_edit_content_ads'
                    ),
                    execute: edit,
                },
                clone: {
                    name: 'Clone',
                    value: 'clone',
                    hasPermission: gridApi.hasPermission(
                        'zemauth.can_clone_contentads'
                    ),
                    internal: gridApi.isPermissionInternal(
                        'zemauth.can_clone_contentads'
                    ),
                    execute: clone,
                },
            };

            // prettier-ignore
            function getActions() { // eslint-disable-line complexity
                var metaData = gridApi.getMetaData();
                if (
                    metaData.level === constants.level.AD_GROUPS &&
                    metaData.breakdown === constants.breakdown.CONTENT_AD
                ) {
                    return [
                        ACTIONS.pause,
                        ACTIONS.enable,
                        ACTIONS.clone,
                        ACTIONS.download,
                        {
                            name: 'Archive',
                            value: 'archive',
                            hasPermission: gridApi.hasPermission(
                                'zemauth.archive_restore_entity'
                            ),
                            internal: gridApi.isPermissionInternal(
                                'zemauth.archive_restore_entity'
                            ),
                            notification:
                                'All selected Content Ads will be paused and archived.',
                            execute: archive,
                        },
                        ACTIONS.restore,
                        ACTIONS.edit,
                    ];
                } else if (
                    metaData.level === constants.level.ACCOUNTS &&
                    metaData.breakdown === constants.breakdown.CAMPAIGN
                ) {
                    return [
                        {
                            name: 'Archive',
                            value: 'archive',
                            hasPermission: gridApi.hasPermission(
                                'zemauth.archive_restore_entity'
                            ),
                            internal: gridApi.isPermissionInternal(
                                'zemauth.archive_restore_entity'
                            ),
                            checkDisabled: checkCanArchive,
                            notificationDisabled:
                                'You can not archive active campaigns',
                            execute: archive,
                        },
                        ACTIONS.restore,
                    ];
                } else if (
                    metaData.level === constants.level.ALL_ACCOUNTS &&
                    metaData.breakdown === constants.breakdown.ACCOUNT
                ) {
                    return [
                        {
                            name: 'Archive',
                            value: 'archive',
                            hasPermission: gridApi.hasPermission(
                                'zemauth.archive_restore_entity'
                            ),
                            internal: gridApi.isPermissionInternal(
                                'zemauth.archive_restore_entity'
                            ),
                            checkDisabled: checkCanArchive,
                            notificationDisabled:
                                'You can not archive active accounts',
                            execute: archive,
                        },
                        ACTIONS.restore,
                    ];
                } else if (
                    metaData.level === constants.level.CAMPAIGNS &&
                    metaData.breakdown === constants.breakdown.AD_GROUP
                ) {
                    return [
                        ACTIONS.pause,
                        ACTIONS.enable,
                        {
                            name: 'Archive',
                            value: 'archive',
                            hasPermission: gridApi.hasPermission(
                                'zemauth.archive_restore_entity'
                            ),
                            internal: gridApi.isPermissionInternal(
                                'zemauth.archive_restore_entity'
                            ),
                            checkDisabled: checkCanArchive,
                            notificationDisabled:
                                'You can not archive active ad groups',
                            execute: archive,
                        },
                        ACTIONS.restore,
                    ];
                } else if (
                    metaData.level === constants.level.AD_GROUPS &&
                    metaData.breakdown === constants.breakdown.MEDIA_SOURCE
                ) {
                    return [ACTIONS.pause, ACTIONS.enable];
                }
            }

            function checkCanArchive() {
                var selection = gridApi.getSelection();
                return !selection.selected.every(function(item) {
                    if (item.level !== 1) {
                        return true;
                    }
                    return (
                        item.data.stats.status.value !==
                        constants.settingsState.ACTIVE
                    );
                });
            }

            function pause(selection) {
                return bulkUpdatedState(
                    selection,
                    constants.settingsState.INACTIVE
                );
            }

            function enable(selection) {
                return bulkUpdatedState(
                    selection,
                    constants.settingsState.ACTIVE
                );
            }

            function archive(selection) {
                var metaData = gridApi.getMetaData();
                return zemEntityService
                    .executeBulkAction(
                        constants.entityAction.ARCHIVE,
                        metaData.level,
                        metaData.breakdown,
                        metaData.id,
                        selection
                    )
                    .then(function(data) {
                        if (metaData.level === constants.level.AD_GROUPS) {
                            notifyArchivingSuccess(
                                data.data.archivedCount,
                                data.data.activeCount
                            );
                        }
                        refreshData(data);
                    }, handleError);
            }

            function restore(selection) {
                var metaData = gridApi.getMetaData();
                return zemEntityService
                    .executeBulkAction(
                        constants.entityAction.RESTORE,
                        metaData.level,
                        metaData.breakdown,
                        metaData.id,
                        selection
                    )
                    .then(function(data) {
                        refreshData(data);
                    }, handleError);
            }

            function edit(selection) {
                var metaData = gridApi.getMetaData();
                return zemEntityService
                    .executeBulkAction(
                        constants.entityAction.EDIT,
                        metaData.level,
                        metaData.breakdown,
                        metaData.id,
                        selection
                    )
                    .then(function(data) {
                        zemUploadService.openEditModal(
                            metaData.id,
                            data.data.batch_id,
                            zemUploadApiConverter.convertCandidatesFromApi(
                                data.data.candidates
                            ),
                            gridApi.loadData
                        );
                    }, handleError);
            }

            function clone(selection) {
                var metaData = gridApi.getMetaData();
                return zemCloneContentService
                    .openCloneModal(metaData.id, selection)
                    .then(function(destinationBatch) {
                        // reloads data in case cloned upload batch is in the same ad group as source content ads
                        if (
                            parseInt(destinationBatch.adGroup.id) ===
                            parseInt(metaData.id)
                        ) {
                            refreshData({});
                        }
                    });
            }

            function download(selection) {
                var metaData = gridApi.getMetaData();
                var url = '/api/ad_groups/' + metaData.id + '/contentads/csv/?';
                url +=
                    'content_ad_ids_selected=' +
                    selection.selectedIds.join(',');
                url +=
                    '&content_ad_ids_not_selected=' +
                    selection.unselectedIds.join(',');
                url +=
                    '&archived=' +
                    !!gridApi.getFilter(
                        gridApi.DS_FILTER.SHOW_ARCHIVED_SOURCES
                    );

                if (selection.filterAll)
                    url += '&select_all=' + selection.filterAll;
                if (selection.filterId)
                    url += '&select_batch=' + selection.filterId;

                $window.open(url, '_blank');
                return $q.resolve();
            }

            function bulkUpdatedState(selection, state) {
                var metaData = gridApi.getMetaData();
                var action =
                    state === constants.settingsState.ACTIVE
                        ? constants.entityAction.ACTIVATE
                        : constants.entityAction.DEACTIVATE;
                return zemEntityService
                    .executeBulkAction(
                        action,
                        metaData.level,
                        metaData.breakdown,
                        metaData.id,
                        selection
                    )
                    .then(function(data) {
                        refreshData(data);
                    }, handleError);
            }

            function notifyArchivingSuccess(archivedCount, activeCount) {
                // FIXME: find better solution for pluralization
                var msg = archivedCount;
                if (archivedCount === 1) {
                    msg += ' Content Ad was archived and it ';
                    msg += activeCount === 1 ? 'was' : "wasn't";
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

                zemAlertsService.notify(
                    constants.notificationType.warning,
                    msg,
                    true
                );
            }

            function refreshData(data) {
                if (data.data && angular.isArray(data.data.rows)) {
                    gridApi.updateData(data.data);
                } else {
                    gridApi.loadData();
                }
                gridApi.clearSelection();
            }

            function handleError(data) {
                zemAlertsService.notify(
                    constants.notificationType.danger,
                    'Error executing action: ' + data.data.message,
                    true
                );
            }
        }

        return {
            createInstance: function(gridApi) {
                return new BulkActionsService(gridApi);
            },
        };
    });
