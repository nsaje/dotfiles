var commonHelpers = require('../../../../shared/helpers/common.helpers');
var ENTITY_MANAGER_CONFIG = require('../../../../features/entity-manager/entity-manager.config')
    .ENTITY_MANAGER_CONFIG;

angular
    .module('one.widgets')
    .service('zemGridActionsService', function(
        $q,
        zemUploadService,
        zemUploadApiConverter,
        zemEntityService,
        zemToastsService,
        zemCloneAdGroupService,
        zemCloneCampaignService,
        zemCloneContentService,
        $window,
        zemGridBulkPublishersActionsService,
        zemModalsService,
        zemUtils,
        $location,
        zemGridConstants,
        zemPermissions
    ) {
        // eslint-disable-line max-len

        var BUTTONS = {
            edit: {
                name: 'Edit',
                type: 'edit',
                action: editRow,
            },
            archive: {
                name: 'Archive',
                type: 'archive',
                action: archiveRow,
            },
            unarchive: {
                name: 'Restore',
                type: 'restore',
                action: restoreRow,
            },
            clone: {
                name: 'Clone',
                type: 'clone',
                action: cloneRow,
            },
            download: {
                name: 'Download',
                type: 'download',
                action: downloadRow,
            },
            settings: {
                name: 'Settings',
                type: 'settings',
                action: openSettingsRow,
            },
        };

        // Public API
        this.getButtons = getButtons;
        this.isStateSwitchVisible = isStateSwitchVisible;
        this.getStateCautionMessage = getStateCautionMessage;
        this.getWidth = getWidth;

        // prettier-ignore
        function getButtons(level, breakdown, row) { // eslint-disable-line complexity
            var buttons = [];
            function addArchiveUnarchive() {
                if (row.data.archived) {
                    buttons.push(BUTTONS.unarchive);
                } else {
                    buttons.push(BUTTONS.archive);
                }
            }
            function addPublisherActions(row, actions) {
                angular.copy(actions).forEach(function(action) {
                    if (row.data.stats.exchange) {
                        if (
                            row.data.stats.exchange.value ===
                            constants.sourceTypeName.YAHOO
                        ) {
                            return;
                        }
                        if (
                            row.data.stats.exchange.value ===
                                constants.sourceTypeName.OUTBRAIN &&
                            action.level !==
                                constants.publisherBlacklistLevel.ACCOUNT
                        ) {
                            return;
                        }
                    }
                    if (!action.hasPermission) {
                        return;
                    }
                    action.action = executePublisherAction;
                    action.type = action.value;
                    buttons.push(action);
                });
            }

            if (
                level === constants.level.ALL_ACCOUNTS &&
                breakdown === constants.breakdown.ACCOUNT
            ) {
                buttons.push(BUTTONS.settings);
                addArchiveUnarchive();
            } else if (
                (level === constants.level.ALL_ACCOUNTS || level === constants.level.ACCOUNTS) &&
                breakdown === constants.breakdown.CAMPAIGN
            ) {
                buttons.push(BUTTONS.settings);
                if (zemPermissions.hasPermission('zemauth.can_clone_campaigns')) {
                    buttons.push(BUTTONS.clone);
                }
                addArchiveUnarchive();
            } else if (
                (level === constants.level.ACCOUNTS || level === constants.level.CAMPAIGNS) &&
                breakdown === constants.breakdown.AD_GROUP
            ) {
                buttons.push(BUTTONS.settings);
                buttons.push(BUTTONS.clone);
                addArchiveUnarchive();
            } else if (
                level === constants.level.AD_GROUPS &&
                breakdown === constants.breakdown.CONTENT_AD
            ) {
                if (!row.data.archived) {
                    buttons.push(BUTTONS.edit);
                }
                buttons.push(BUTTONS.clone);
                buttons.push(BUTTONS.download);
                addArchiveUnarchive();
            } else if (breakdown === constants.breakdown.PUBLISHER) {
                if (
                    row.data.stats.status &&
                    row.data.stats.status.value ===
                        constants.publisherTargetingStatus.BLACKLISTED
                ) {
                    addPublisherActions(
                        row,
                        zemGridBulkPublishersActionsService.getUnlistActions(
                            level
                        )
                    );
                }
                addPublisherActions(
                    row,
                    zemGridBulkPublishersActionsService.getBlacklistActions(
                        level
                    )
                );
            }
            return buttons;
        }

        function isStateSwitchVisible(level, breakdown, row) {
            if (row.data.archived) {
                return false;
            }

            if (level === constants.level.AD_GROUPS) {
                if (breakdown === constants.breakdown.CONTENT_AD) {
                    return true;
                }
                if (breakdown === constants.breakdown.MEDIA_SOURCE) {
                    return true;
                }
            }
            if (level === constants.level.CAMPAIGNS) {
                if (breakdown === constants.breakdown.AD_GROUP) {
                    return true;
                }
            }

            return false;
        }

        function getStateCautionMessage(row) {
            if (
                row.data.archived ||
                !row.data.stats ||
                !row.data.stats.status ||
                !row.data.stats.status.important ||
                !row.data.stats.status.popoverMessage
            ) {
                return null;
            }

            return row.data.stats.status.popoverMessage;
        }

        function getWidth(level, breakdown, row) {
            var width = 0;
            if (isStateSwitchVisible(level, breakdown, row)) {
                width += 54;
            }
            var buttons = getButtons(level, breakdown, row);
            if (buttons.length > 0) {
                width += 40;
                if (
                    buttons.length > 1 &&
                    breakdown !== constants.breakdown.PUBLISHER
                ) {
                    width += 40;
                }
            }
            if (getStateCautionMessage(row)) {
                width += 10;
            }
            return width;
        }

        function editRow(row, grid) {
            return grid.meta.dataService.editRow(row).then(function(response) {
                zemUploadService.openEditModal(
                    grid.meta.data.id,
                    response.data.batch_id,
                    zemUploadApiConverter.convertCandidatesFromApi(
                        response.data.candidates
                    ),
                    grid.meta.api.loadData
                );
            });
        }

        function cloneRow(row, grid) {
            var parentId =
                row.level === zemGridConstants.gridRowLevel.BASE
                    ? parseInt(grid.meta.data.id)
                    : parseInt(row.parent.id);
            if (row.entity.type === constants.entityType.CAMPAIGN) {
                zemCloneCampaignService
                    .openCloneModal(
                        row.entity.id,
                        row.data.stats.breakdown_name.value
                    )
                    .then(function() {
                        grid.meta.api.loadData();
                    });
            } else if (row.entity.type === constants.entityType.AD_GROUP) {
                zemCloneAdGroupService
                    .openCloneModal(parentId, row.entity.id)
                    .then(function() {
                        grid.meta.api.loadData();
                    });
            } else if (row.entity.type === constants.entityType.CONTENT_AD) {
                zemCloneContentService
                    .openCloneModal(parentId, {
                        selectedIds: [row.entity.id],
                    })
                    .then(function(batchData) {
                        zemUploadService
                            .openCloneEditModal(
                                parentId,
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
                                        ) === parseInt(parentId)
                                    ) {
                                        grid.meta.api.loadData();
                                    }
                                    zemCloneContentService.openResultsModal(
                                        batchData.destinationBatch
                                    );
                                }
                            });
                    }, handleError);
            }

            // calling component hides loader on promise resolve, we do not want loader when opening modal
            return $q.resolve();
        }

        function archiveRow(row, grid) {
            var confirmTitle = 'Do you want to archive {entity} {name}?';
            var confirmText =
                "While archived, the {entity} will be hidden. You won't be able to review {entity} statistics or manage it. You will be able to restore an archived {entity}, which will bring back all it's settings and statistics."; // eslint-disable-line max-len
            confirmText = confirmText.replace(
                /{entity}/g,
                getEntityTypeText(row.entity.type)
            );
            confirmTitle = confirmTitle.replace(
                /{entity}/g,
                getEntityTypeText(row.entity.type)
            );
            confirmTitle = confirmTitle.replace(
                /{name}/g,
                row.data.stats.breakdown_name.value
            );

            return zemModalsService
                .openConfirmModal(confirmText, confirmTitle)
                .then(function() {
                    if (row.entity.type === constants.entityType.CONTENT_AD) {
                        return zemEntityService
                            .executeBulkAction(
                                constants.entityAction.ARCHIVE,
                                grid.meta.data.level,
                                grid.meta.data.breakdown,
                                grid.meta.data.id,
                                {
                                    selectedIds: [row.entity.id],
                                }
                            )
                            .then(function() {
                                grid.meta.api.loadData();
                            }, handleError);
                    }
                    return zemEntityService
                        .executeAction(
                            constants.entityAction.ARCHIVE,
                            row.entity.type,
                            row.entity.id
                        )
                        .then(function() {
                            grid.meta.api.loadData();
                        }, handleError);
                });
        }

        function getEntityTypeText(entityType) {
            if (entityType === constants.entityType.ACCOUNT) {
                return 'account';
            } else if (entityType === constants.entityType.CAMPAIGN) {
                return 'campaign';
            } else if (entityType === constants.entityType.AD_GROUP) {
                return 'ad group';
            } else if (entityType === constants.entityType.CONTENT_AD) {
                return 'content ad';
            }
        }

        function restoreRow(row, grid) {
            if (row.entity.type === constants.entityType.CONTENT_AD) {
                return zemEntityService
                    .executeBulkAction(
                        constants.entityAction.RESTORE,
                        grid.meta.data.level,
                        grid.meta.data.breakdown,
                        grid.meta.data.id,
                        {
                            selectedIds: [row.entity.id],
                        }
                    )
                    .then(function() {
                        grid.meta.api.loadData();
                    }, handleError);
            }
            return zemEntityService
                .executeAction(
                    constants.entityAction.RESTORE,
                    row.entity.type,
                    row.entity.id
                )
                .then(function() {
                    grid.meta.api.loadData();
                }, handleError);
        }

        function downloadRow(row, grid) {
            var url =
                '/api/ad_groups/' + grid.meta.data.id + '/contentads/csv/?';
            url += 'content_ad_ids_selected=' + row.entity.id;
            url +=
                '&archived=' +
                !!grid.meta.api.getFilter(
                    grid.meta.api.DS_FILTER.SHOW_ARCHIVED_SOURCES
                );

            $window.open(url, '_blank');
            // calling component hides loader on promise resolve
            return $q.resolve();
        }

        function openSettingsRow(row) {
            var searchParams = {};
            searchParams[ENTITY_MANAGER_CONFIG.settingsQueryParam] = true;
            searchParams[ENTITY_MANAGER_CONFIG.levelQueryParam] =
                row.entity.type;
            searchParams[ENTITY_MANAGER_CONFIG.idQueryParam] = row.entity.id;

            $location.search(searchParams).replace();

            // calling component hides loader on promise resolve
            return $q.resolve();
        }

        function executePublisherAction(row, grid, action) {
            return zemGridBulkPublishersActionsService
                .execute(action, false, {selected: [row], unselected: []})
                .then(function() {
                    grid.meta.api.loadData();
                }, handleError);
        }

        function handleError(data) {
            zemToastsService.error(data.data.message);
        }
    });
