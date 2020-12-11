angular
    .module('one.widgets')
    .factory('zemGridColumnsService', function(
        zemGridConstants,
        zemGridStorageService,
        zemUtils,
        zemCostModeService
    ) {
        // eslint-disable-line max-len

        function ColumnsService(grid) {
            var pubsub = grid.meta.pubsub;

            initialize();

            //
            // Public API
            //
            this.destroy = destroy;
            this.getVisibleColumns = getVisibleColumns;
            this.setVisibleColumns = setVisibleColumns;
            this.isColumnAvailable = isColumnAvailable;
            this.getColumnsToToggle = getColumnsToToggle;
            this.findColumnInCategories = findColumnInCategories;
            this.getTogglableColumns = getTogglableColumns;

            var onMetaDataUpdatedHandler;
            var onDataUpdatedHandler;

            function initialize() {
                onMetaDataUpdatedHandler = pubsub.register(
                    pubsub.EVENTS.METADATA_UPDATED,
                    null,
                    initializeColumns
                );
                onDataUpdatedHandler = pubsub.register(
                    pubsub.EVENTS.DATA_UPDATED,
                    null,
                    initializeColumnsState
                );
            }

            function destroy() {
                if (onMetaDataUpdatedHandler) onMetaDataUpdatedHandler();
                if (onDataUpdatedHandler) onDataUpdatedHandler();
            }

            function initializeColumns() {
                zemGridStorageService.loadColumns(grid);
                initializeColumnsState();
            }

            function initializeColumnsState() {
                var breakdowns = grid.meta.api
                    .getBreakdown()
                    .map(function(breakdown) {
                        return breakdown.query;
                    });
                grid.header.columns.forEach(function(column) {
                    column.disabled = !isColumnAvailable(
                        column,
                        grid.meta.data.level,
                        breakdowns
                    );
                });
                pubsub.notify(grid.meta.pubsub.EVENTS.EXT_COLUMNS_UPDATED);
            }

            function isColumnAvailable(column, level, breakdowns) {
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
                                Object.prototype.hasOwnProperty.call(
                                    col.data,
                                    'autoSelect'
                                ) &&
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
                for (var i = 0; i < categories.length; ++i) {
                    var category = categories[i];
                    currentColumn =
                        category.columns.find(function(column) {
                            return columnField === column.field;
                        }) ||
                        findColumnInCategories(
                            category.subcategories,
                            columnField
                        );
                    if (currentColumn) return currentColumn;
                }
                return null;
            }
        }

        return {
            createInstance: function(grid) {
                return new ColumnsService(grid);
            },
        };
    });
