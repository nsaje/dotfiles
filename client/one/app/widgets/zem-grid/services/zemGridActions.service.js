angular.module('one.widgets').service('zemGridActionsService', function ($q, zemUploadService, zemUploadApiConverter, zemEntityService, zemToastsService, zemCloneAdGroupService, zemCloneContentService, $window, zemGridBulkPublishersActionsService) {  // eslint-disable-line max-len

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
    };

    // Public API
    this.getButtons = getButtons;
    this.isStateSwitchVisible = isStateSwitchVisible;
    this.getWidth = getWidth;

    function getButtons (level, breakdown, row) {
        var buttons = [];
        function addArchiveUnarchive () {
            if (row.data.archived) {
                buttons.push(BUTTONS.unarchive);
            } else {
                buttons.push(BUTTONS.archive);
            }
        }
        function addPublisherActions (actions) {
            actions.forEach(function (action) {
                action.action = executePublisherAction;
                buttons.push(action);
            });
        }

        if (level === constants.level.ALL_ACCOUNTS && breakdown === constants.breakdown.ACCOUNT) {
            addArchiveUnarchive();
        } else if (level === constants.level.ACCOUNTS && breakdown === constants.breakdown.CAMPAIGN) {
            addArchiveUnarchive();
        } else if (level === constants.level.CAMPAIGNS && breakdown === constants.breakdown.AD_GROUP) {
            addArchiveUnarchive();
            buttons.push(BUTTONS.clone);
        } else if (level === constants.level.AD_GROUPS && breakdown === constants.breakdown.CONTENT_AD) {
            if (!row.data.archived) {
                buttons.push(BUTTONS.edit);
            }
            addArchiveUnarchive();
            buttons.push(BUTTONS.clone);
            buttons.push(BUTTONS.download);
        } else if (breakdown === constants.breakdown.PUBLISHER) {
            if (row.data.stats.status &&
                    row.data.stats.status.value === constants.publisherTargetingStatus.BLACKLISTED) {
                addPublisherActions(zemGridBulkPublishersActionsService.getUnlistActions(level));
            }
            addPublisherActions(zemGridBulkPublishersActionsService.getBlacklistActions(level));
        }
        return buttons;
    }

    function isStateSwitchVisible (level, breakdown, row) {
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

    function getWidth (level, breakdown, row) {
        var width = 0;
        if (isStateSwitchVisible(level, breakdown, row)) {
            width += 40;
        }
        var buttons = getButtons(level, breakdown, row);
        if (buttons.length > 0) {
            width += 34;
            if (buttons.length > 1 && breakdown !== constants.breakdown.PUBLISHER) {
                width += 34;
            }
        }
        return width;
    }

    function editRow (row, grid) {
        return grid.meta.dataService.editRow(row).then(function (response) {
            zemUploadService.openEditModal(
                grid.meta.data.id,
                response.data.batch_id,
                zemUploadApiConverter.convertCandidatesFromApi(response.data.candidates),
                grid.meta.api.loadData
            );
        });
    }

    function cloneRow (row, grid) {
        if (row.entity.type === constants.entityType.AD_GROUP) {
            zemCloneAdGroupService.openCloneModal(
                grid.meta.data.id,
                row.entity.id
            ).then(function () {
                grid.meta.api.loadData();
            });
        } else if (row.entity.type === constants.entityType.CONTENT_AD) {
            zemCloneContentService.openCloneModal(
                grid.meta.data.id,
                {
                    selectedIds: [row.entity.id],
                }
            ).then(function () {
                grid.meta.api.loadData();
            });
        }

        // calling component hides loader on promise resolve, we do not want loader when opening modal
        return $q.resolve();
    }

    function archiveRow (row, grid) {
        if (row.entity.type === constants.entityType.CONTENT_AD) {
            return zemEntityService.executeBulkAction(
                constants.entityAction.ARCHIVE,
                grid.meta.data.level,
                grid.meta.data.breakdown,
                grid.meta.data.id,
                {
                    selectedIds: [row.entity.id],
                }
            ).then(function () {
                grid.meta.api.loadData();
            }, handleError);
        }
        return zemEntityService.executeAction(
            constants.entityAction.ARCHIVE,
            row.entity.type,
            row.entity.id
        ).then(function () {
            grid.meta.api.loadData();
        }, handleError);
    }

    function restoreRow (row, grid) {
        if (row.entity.type === constants.entityType.CONTENT_AD) {
            return zemEntityService.executeBulkAction(
                constants.entityAction.RESTORE,
                grid.meta.data.level,
                grid.meta.data.breakdown,
                grid.meta.data.id,
                {
                    selectedIds: [row.entity.id],
                }
            ).then(function () {
                grid.meta.api.loadData();
            }, handleError);
        }
        return zemEntityService.executeAction(
            constants.entityAction.RESTORE,
            row.entity.type,
            row.entity.id
        ).then(function () {
            grid.meta.api.loadData();
        }, handleError);
    }

    function downloadRow (row, grid) {
        var url = '/api/ad_groups/' + grid.meta.data.id + '/contentads/csv/?';
        url += 'content_ad_ids_selected=' + row.entity.id;
        url += '&archived=' + !!grid.meta.api.getFilter(grid.meta.api.DS_FILTER.SHOW_ARCHIVED_SOURCES);

        $window.open(url, '_blank');
        // calling component hides loader on promise resolve
        return $q.resolve();
    }

    function executePublisherAction (row, grid, action) {
        return zemGridBulkPublishersActionsService.execute(
            action,
            false,
            {selected: [row], unselected: []}
        ).then(function () {
            grid.meta.api.loadData();
        }, handleError);
    }

    function handleError (data) {
        zemToastsService.error(data.data.message);
    }
});
