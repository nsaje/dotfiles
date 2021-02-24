var getOffset = require('../../../../shared/helpers/pagination.helper')
    .getOffset;

angular
    .module('one.widgets')
    .factory('zemGridApi', function(zemGridUIService, zemGridConstants) {
        // eslint-disable-line max-len

        //
        // GridApi provides interface for interaction with zem-grid
        // Reference can be sent to non-grid components (e.g. zem-grid-column-selector, zem-grid-breakdown-selector),
        // or may be passed back to calling controller to enable interaction between them.
        //

        function GridApi(grid) {
            var pubsub = grid.meta.pubsub;

            // Grid Object API
            this.isInitialized = isInitialized;
            this.getMetaData = getMetaData;
            this.getRenderingEngine = getRenderingEngine;
            this.getRows = getRows;
            this.getColumns = getColumns;
            this.getCategorizedColumns = getCategorizedColumns;

            // Data service API
            this.initialize = grid.meta.dataService.initialize;
            this.loadMetaData = grid.meta.dataService.loadMetaData;
            this.loadData = loadData;
            this.replaceDataSource = grid.meta.dataService.replaceDataSource;
            this.saveData = grid.meta.dataService.saveData;
            this.saveDataQueued = grid.meta.dataService.saveDataQueued;
            this.DS_FILTER = grid.meta.dataService.DS_FILTER;
            this.setBreakdown = grid.meta.dataService.setBreakdown;
            this.getBreakdown = grid.meta.dataService.getBreakdown;
            this.getBreakdownLevel = grid.meta.dataService.getBreakdownLevel;
            this.setOrder = grid.meta.dataService.setOrder;
            this.getOrder = grid.meta.dataService.getOrder;
            this.setFilter = grid.meta.dataService.setFilter;
            this.getFilter = grid.meta.dataService.getFilter;
            this.updateData = grid.meta.dataService.updateData;
            this.updateRowStats = grid.meta.dataService.updateRowStats;
            this.isSaveRequestInProgress =
                grid.meta.dataService.isSaveRequestInProgress;
            this.editRow = grid.meta.dataService.editRow;

            // Selection service API
            this.isRowSelected = grid.meta.selectionService.isRowSelected;
            this.isRowSelectable = grid.meta.selectionService.isRowSelectable;
            this.setRowSelection = grid.meta.selectionService.setRowSelection;
            this.isSelectionEmpty = grid.meta.selectionService.isSelectionEmpty;
            this.getSelection = grid.meta.selectionService.getSelection;
            this.clearSelection = grid.meta.selectionService.clearSelection;
            this.setSelection = grid.meta.selectionService.setSelection;
            this.setSelectionFilter = grid.meta.selectionService.setFilter;
            this.getSelectionOptions = grid.meta.selectionService.getConfig;
            this.setSelectionOptions = grid.meta.selectionService.setConfig;
            this.getCustomFilters = grid.meta.selectionService.getCustomFilters;

            // Columns service API
            this.getVisibleColumns = grid.meta.columnsService.getVisibleColumns;
            this.setVisibleColumns = grid.meta.columnsService.setVisibleColumns;
            this.isColumnAvailable = grid.meta.columnsService.isColumnAvailable;
            this.getColumnsToToggle =
                grid.meta.columnsService.getColumnsToToggle;
            this.findColumnInCategories =
                grid.meta.columnsService.findColumnInCategories;
            this.getTogglableColumns =
                grid.meta.columnsService.getTogglableColumns;

            this.refreshUI = refreshUI;

            // Listeners - pubsub rewiring
            this.onMetaDataUpdated = onMetaDataUpdated;
            this.onDataUpdated = onDataUpdated;
            this.onDataUpdatedError = onDataUpdatedError;
            this.onRowDataUpdated = onRowDataUpdated;
            this.onRowDataUpdatedError = onRowDataUpdatedError;
            this.onColumnsUpdated = onColumnsUpdated;
            this.onSelectionUpdated = onSelectionUpdated;

            function isInitialized() {
                return grid.meta.initialized;
            }

            function getMetaData() {
                return grid.meta.data;
            }

            function getRenderingEngine() {
                return grid.meta.renderingEngine;
            }

            function loadData(row, offset, limit) {
                if (
                    grid.meta.renderingEngine ===
                    zemGridConstants.gridRenderingEngineType.SMART_GRID
                ) {
                    return grid.meta.dataService.loadData(
                        null,
                        getOffset(
                            grid.meta.paginationOptions.page,
                            grid.meta.paginationOptions.pageSize
                        ),
                        grid.meta.paginationOptions.pageSize
                    );
                }
                return grid.meta.dataService.loadData(row, offset, limit);
            }

            function getRows() {
                var rows = grid.body.rows.slice();
                if (grid.footer.row) {
                    rows.push(grid.footer.row);
                }
                return rows;
            }

            function getColumns() {
                return grid.header.columns;
            }

            function getCategoryColumns(zemCostModeService, category, columns) {
                var costMode = zemCostModeService.getCostMode();

                return columns.filter(function(column) {
                    var inCategory =
                        category.fields.indexOf(column.field) !== -1;
                    if (
                        !inCategory ||
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

            function getCategory(zemCostModeService, category, columns) {
                var categoryColumns = getCategoryColumns(
                        zemCostModeService,
                        category,
                        columns
                    ),
                    subcategories = [];

                if (category.hasOwnProperty('subcategories')) {
                    subcategories = category.subcategories.map(function(
                        subcategory
                    ) {
                        return getCategory(
                            zemCostModeService,
                            subcategory,
                            columns
                        );
                    });
                }

                return {
                    name: category.name,
                    description: category.description,
                    type: category.type,
                    subcategories: subcategories,
                    columns: categoryColumns,
                    isNewFeature: category.isNewFeature,
                    helpText: category.helpText,
                };
            }

            function getCategorizedColumns(zemCostModeService, columns) {
                var categories = [];
                getMetaData().categories.forEach(function(category) {
                    var newCategory = getCategory(
                        zemCostModeService,
                        category,
                        columns
                    );
                    if (isNotEmptyCategory(newCategory)) {
                        categories.push(newCategory);
                    }
                });
                return categories;
            }

            function isNotEmptyCategory(category) {
                if (category.subcategories) {
                    for (var i = 0; i < category.subcategories.length; i++) {
                        if (isNotEmptyCategory(category.subcategories[i])) {
                            return true;
                        }
                    }
                }
                return category.columns.length > 0;
            }

            function refreshUI() {
                zemGridUIService.resizeGridColumns(grid);
                zemGridUIService.updateStickyElements(grid);
                zemGridUIService.updatePivotColumns(
                    grid,
                    grid.body.ui.scrolleft || 0
                );
            }

            function onMetaDataUpdated(scope, callback) {
                return registerListener(
                    pubsub.EVENTS.METADATA_UPDATED,
                    scope,
                    callback
                );
            }

            function onDataUpdated(scope, callback) {
                return registerListener(
                    pubsub.EVENTS.DATA_UPDATED,
                    scope,
                    callback
                );
            }

            function onDataUpdatedError(scope, callback) {
                return registerListener(
                    pubsub.EVENTS.DATA_UPDATED_ERROR,
                    scope,
                    callback
                );
            }

            function onRowDataUpdated(scope, callback) {
                return registerListener(
                    pubsub.EVENTS.ROW_UPDATED,
                    scope,
                    callback
                );
            }

            function onRowDataUpdatedError(scope, callback) {
                return registerListener(
                    pubsub.EVENTS.ROW_UPDATED_ERROR,
                    scope,
                    callback
                );
            }

            function onColumnsUpdated(scope, callback) {
                return registerListener(
                    pubsub.EVENTS.EXT_COLUMNS_UPDATED,
                    scope,
                    callback
                );
            }

            function onSelectionUpdated(scope, callback) {
                return registerListener(
                    pubsub.EVENTS.EXT_SELECTION_UPDATED,
                    scope,
                    callback
                );
            }

            function registerListener(event, scope, callback) {
                return pubsub.register(event, scope, callback);
            }
        }

        return {
            createInstance: function(grid) {
                return new GridApi(grid);
            },
        };
    });
