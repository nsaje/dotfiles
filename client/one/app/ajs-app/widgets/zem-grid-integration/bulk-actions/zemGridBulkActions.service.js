var commonHelpers = require('../../../../shared/helpers/common.helpers');
var AlertType = require('../../../../app.constants').AlertType;

angular
    .module('one.widgets')
    .factory('zemGridBulkActionsService', function(
        $q,
        $window,
        zemEntityService,
        zemGridEndpointColumns,
        zemGridConstants,
        zemAlertsStore,
        zemUploadService,
        zemUploadApiConverter,
        zemCloneContentService,
        zemUtils,
        zemAuthStore,
        zemNavigationNewService,
        zemNavigationService
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
                    disabled: false,
                    execute: pause,
                },
                enable: {
                    name: 'Enable',
                    value: 'enable',
                    hasPermission: true,
                    disabled: false,
                    execute: enable,
                },
                download: {
                    name: 'Download',
                    value: 'download',
                    hasPermission: true,
                    disabled: false,
                    execute: download,
                },
                archive: {
                    name: 'Archive',
                    value: 'archive',
                    hasPermission: true,
                    disabled: false,
                    execute: archive,
                },
                restore: {
                    name: 'Restore',
                    value: 'restore',
                    hasPermission: true,
                    disabled: false,
                    execute: restore,
                },
                edit: {
                    name: 'Edit',
                    value: 'edit',
                    hasPermission: true,
                    internal: false,
                    disabled: false,
                    execute: edit,
                },
                clone: {
                    name: 'Clone',
                    value: 'clone',
                    hasPermission: true,
                    internal: false,
                    disabled: false,
                    execute: clone,
                },
            };

            // prettier-ignore
            function getActions() { // eslint-disable-line complexity
                var metaData = gridApi.getMetaData();
                var selection = gridApi.getSelection();
                var hasReadOnlyAccess = hasReadOnlyAccessOnAnySelectedRow(metaData.level, selection);
                if (
                    metaData.level === constants.level.AD_GROUPS &&
                    metaData.breakdown === constants.breakdown.CONTENT_AD
                ) {
                    return [
                        commonHelpers.patchObject(ACTIONS.pause, {disabled: hasReadOnlyAccess}),
                        commonHelpers.patchObject(ACTIONS.enable, {disabled: hasReadOnlyAccess}),
                        commonHelpers.patchObject(ACTIONS.clone, {disabled: hasReadOnlyAccess}),
                        ACTIONS.download,
                        commonHelpers.patchObject(ACTIONS.archive, {disabled: hasReadOnlyAccess, notification: 'All selected Content Ads will be paused and archived.'}),
                        commonHelpers.patchObject(ACTIONS.restore, {disabled: hasReadOnlyAccess}),
                        commonHelpers.patchObject(ACTIONS.edit, {disabled: hasReadOnlyAccess}),
                    ];
                } else if (
                    metaData.level === constants.level.ACCOUNTS &&
                    metaData.breakdown === constants.breakdown.CAMPAIGN
                ) {
                    return [
                        commonHelpers.patchObject(ACTIONS.archive, {disabled: hasReadOnlyAccess}),
                        commonHelpers.patchObject(ACTIONS.restore,  {disabled: hasReadOnlyAccess}),
                    ];
                } else if (
                    metaData.level === constants.level.ALL_ACCOUNTS &&
                    metaData.breakdown === constants.breakdown.ACCOUNT
                ) {
                    return [
                        commonHelpers.patchObject(ACTIONS.archive, {disabled: hasReadOnlyAccess}),
                        commonHelpers.patchObject(ACTIONS.restore,  {disabled: hasReadOnlyAccess}),
                    ];
                } else if (
                    metaData.level === constants.level.CAMPAIGNS &&
                    metaData.breakdown === constants.breakdown.AD_GROUP
                ) {
                    return [
                        commonHelpers.patchObject(ACTIONS.pause, {disabled: hasReadOnlyAccess}),
                        commonHelpers.patchObject(ACTIONS.enable,  {disabled: hasReadOnlyAccess}),
                        commonHelpers.patchObject(ACTIONS.archive, {disabled: hasReadOnlyAccess}),
                        commonHelpers.patchObject(ACTIONS.restore,  {disabled: hasReadOnlyAccess}),
                    ];
                } else if (
                    metaData.level === constants.level.AD_GROUPS &&
                    metaData.breakdown === constants.breakdown.MEDIA_SOURCE
                ) {
                    return [
                        commonHelpers.patchObject(ACTIONS.pause, {disabled: hasReadOnlyAccess}),
                        commonHelpers.patchObject(ACTIONS.enable,  {disabled: hasReadOnlyAccess}),
                    ];
                }
            }

            function hasReadOnlyAccessOnAnySelectedRow(level, selection) {
                if (
                    selection.type ===
                    zemGridConstants.gridSelectionFilterType.ALL
                ) {
                    if (level !== constants.level.ALL_ACCOUNTS) {
                        var account = zemNavigationNewService.getActiveAccount();
                        return zemAuthStore.hasReadOnlyAccessOn(
                            account.data.agencyId,
                            account.id
                        );
                    }
                    return zemAuthStore.hasReadOnlyAccessOnAnyEntity();
                }

                return selection.selected
                    .filter(function(row) {
                        return row.level === 1;
                    })
                    .some(function(row) {
                        var agencyId = row.data.stats.agency_id
                            ? row.data.stats.agency_id.value
                            : null;
                        var accountId = row.data.stats.account_id
                            ? row.data.stats.account_id.value
                            : null;
                        return zemAuthStore.hasReadOnlyAccessOn(
                            agencyId,
                            accountId
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
                        updateNavigationCachePromise().then(refreshData(data));
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
                        updateNavigationCachePromise().then(refreshData(data));
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
                    .then(function(batchData) {
                        zemUploadService
                            .openCloneEditModal(
                                metaData.id,
                                batchData.destinationBatch.id,
                                batchData.destinationBatch.name,
                                zemUploadApiConverter.convertCandidatesFromApi(
                                    zemUtils.convertToUnderscore(
                                        batchData.candidates
                                    )
                                )
                            )
                            .then(function(success) {
                                if (
                                    !(
                                        commonHelpers.isDefined(success) &&
                                        success === false
                                    )
                                ) {
                                    // reloads data in case cloned upload batch is in the same ad group as source content ads
                                    if (
                                        parseInt(
                                            batchData.destinationBatch.adGroup
                                                .id
                                        ) === parseInt(metaData.id)
                                    ) {
                                        refreshData({});
                                    }
                                    zemCloneContentService.openResultsModal(
                                        batchData.destinationBatch
                                    );
                                }
                            });
                    }, handleError);
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

                zemAlertsStore.registerAlert({
                    type: AlertType.WARNING,
                    message: msg,
                    isClosable: true,
                });
            }

            function refreshData(data) {
                gridApi.clearSelection();
                if (data.data && angular.isArray(data.data.rows)) {
                    gridApi.updateData(data.data);
                } else {
                    gridApi.loadData();
                }
            }

            function handleError(data) {
                zemAlertsStore.registerAlert({
                    type: AlertType.DANGER,
                    message: 'Error executing action: ' + data.data.message,
                    isClosable: true,
                });
            }

            function updateNavigationCachePromise() {
                var deferred = $q.defer();
                zemNavigationService.reload().then(function() {
                    deferred.resolve();
                });
                return deferred.promise;
            }
        }

        return {
            createInstance: function(gridApi) {
                return new BulkActionsService(gridApi);
            },
        };
    });
