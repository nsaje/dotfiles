angular
    .module('one.widgets')
    .factory('zemGridColumnsService', function(
        zemGridConstants,
        zemGridStorageService,
        zemUtils,
        zemCostModeService,
        zemNavigationNewService,
        zemGridEndpointColumns
    ) {
        // eslint-disable-line max-len

        function ColumnsService(grid) {
            var pubsub = grid.meta.pubsub;

            initialize();

            //
            // Public API
            //
            this.getVisibleColumns = getVisibleColumns;
            this.setVisibleColumns = setVisibleColumns;
            this.getColumnsToToggle = getColumnsToToggle;
            this.findColumnInCategories = findColumnInCategories;
            this.getTogglableColumns = getTogglableColumns;

            function initialize() {
                pubsub.register(
                    pubsub.EVENTS.METADATA_UPDATED,
                    null,
                    initializeColumns
                );
                pubsub.register(
                    pubsub.EVENTS.DATA_UPDATED,
                    null,
                    initializeColumnsState
                );
                zemCostModeService.onCostModeUpdate(function() {
                    pubsub.notify(grid.meta.pubsub.EVENTS.EXT_COLUMNS_UPDATED);
                    pubsub.notify(grid.meta.pubsub.EVENTS.METADATA_UPDATED);
                });
                zemNavigationNewService.onUsesBCMv2Update(function() {
                    pubsub.notify(grid.meta.pubsub.EVENTS.EXT_COLUMNS_UPDATED);
                    pubsub.notify(grid.meta.pubsub.EVENTS.METADATA_UPDATED);
                });
            }

            function initializeColumns() {
                zemGridStorageService.loadColumns(grid);
                initializeColumnsState();
            }

            function initializeColumnsState() {
                var breakdowns = grid.meta.dataService
                    .getBreakdown()
                    .map(function(breakdown) {
                        return breakdown.query;
                    });
                var activeEntity = zemNavigationNewService.getActiveEntity();
                grid.header.columns.forEach(function(column) {
                    column.disabled = !isColumnAvailable(
                        column,
                        grid.meta.data.level,
                        breakdowns,
                        activeEntity
                    );
                });
                pubsub.notify(grid.meta.pubsub.EVENTS.EXT_COLUMNS_UPDATED);
            }

            function isColumnAvailable(
                column,
                level,
                breakdowns,
                activeEntity
            ) {
                if (
                    isColumnBidSettingAndShouldBeExcluded(column, activeEntity)
                ) {
                    return false;
                }

                if (!column.data.exceptions) {
                    return true;
                }

                if (column.data.exceptions.custom) {
                    for (
                        var i = 0;
                        i < column.data.exceptions.custom.length;
                        ++i
                    ) {
                        var customException = column.data.exceptions.custom[i];
                        if (
                            customException.level === level &&
                            customException.breakdown === breakdowns[0]
                        ) {
                            return customException.shown;
                        }
                    }
                }

                if (column.data.exceptions.breakdowns) {
                    return zemUtils.intersects(
                        column.data.exceptions.breakdowns,
                        breakdowns
                    );
                }

                return true;
            }

            function isColumnBidSettingAndShouldBeExcluded(
                column,
                activeEntity
            ) {
                if (
                    column.field !==
                        zemGridEndpointColumns.COLUMNS.bidCpcSetting.field &&
                    column.field !==
                        zemGridEndpointColumns.COLUMNS.bidCpmSetting.field
                ) {
                    return false;
                }

                if (
                    !activeEntity ||
                    !activeEntity.data ||
                    activeEntity.type !== constants.entityType.AD_GROUP
                ) {
                    return true;
                }

                if (
                    column.field ===
                        zemGridEndpointColumns.COLUMNS.bidCpcSetting.field &&
                    activeEntity.data.bidding_type !== constants.biddingType.CPC
                ) {
                    return true;
                } else if (
                    column.field ===
                        zemGridEndpointColumns.COLUMNS.bidCpmSetting.field &&
                    activeEntity.data.bidding_type !== constants.biddingType.CPM
                ) {
                    return true;
                }
            }

            function getVisibleColumns() {
                var visibleColumns = grid.header.columns.filter(function(
                    column
                ) {
                    return column.visible && !column.disabled;
                });

                // Add grid-only (non-data) columns
                if (
                    grid.meta.options.selection &&
                    grid.meta.options.selection.enabled
                ) {
                    visibleColumns.unshift({
                        type: zemGridConstants.gridColumnTypes.CHECKBOX,
                    });
                }
                return visibleColumns;
            }

            function setVisibleColumns(toggledColumns, visible, allColumns) {
                getColumnsToToggle(toggledColumns, allColumns).forEach(function(
                    column
                ) {
                    column.visible = visible;
                });

                zemGridStorageService.saveColumns(grid);
                pubsub.notify(grid.meta.pubsub.EVENTS.EXT_COLUMNS_UPDATED);
            }

            function getColumnsToToggle(toggledColumns, allColumns) {
                if (!toggledColumns) {
                    return [];
                }
                var costMode = zemCostModeService.getCostMode();
                var autoSelectableColumns = [];

                if (!Array.isArray(toggledColumns)) {
                    toggledColumns = [toggledColumns];
                }

                if (allColumns) {
                    toggledColumns.forEach(function(toggledColumn) {
                        allColumns.forEach(function(col) {
                            if (
                                col.data.hasOwnProperty('autoSelect') &&
                                col.data.autoSelect === toggledColumn.field
                            ) {
                                if (
                                    zemCostModeService.isTogglableCostMode(
                                        col.data.costMode
                                    )
                                ) {
                                    if (col.data.costMode === costMode) {
                                        autoSelectableColumns.push(col);
                                    }
                                } else {
                                    autoSelectableColumns.push(col);
                                }
                            }
                        });
                    });
                }

                return toggledColumns.concat(autoSelectableColumns);
            }

            function getTogglableColumns(allColumns) {
                var costMode = zemCostModeService.getCostMode();
                return allColumns.filter(function(column) {
                    if (
                        column.disabled ||
                        !column.data.shown ||
                        column.data.permanent
                    )
                        return false;
                    if (
                        zemCostModeService.isTogglableCostMode(
                            column.data.costMode
                        )
                    ) {
                        return column.data.costMode === costMode;
                    }
                    return true;
                });
            }

            function findColumnInCategories(categories, columnField) {
                var currentColumn;
                categories.some(function(category) {
                    currentColumn = category.columns.find(function(column) {
                        return columnField === column.field;
                    });
                    return currentColumn;
                });
                return (
                    currentColumn ||
                    findColumnInSubCategories(categories, columnField)
                );
            }

            function findColumnInSubCategories(categories, columnField) {
                var column;
                categories.some(function(category) {
                    if (category.subcategories.length > 0) {
                        category.subcategories.some(function(subCategory) {
                            column = subCategory.columns.find(function(
                                subColumn
                            ) {
                                return subColumn.field === columnField;
                            });
                            return column;
                        });
                        return column;
                    }
                });
                return column;
            }
        }

        return {
            createInstance: function(grid) {
                return new ColumnsService(grid);
            },
        };
    });
