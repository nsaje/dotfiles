angular.module('one.widgets').factory('zemGridApi', function(zemGridUIService) {
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
        this.getRows = getRows;
        this.getColumns = getColumns;
        this.getCategorizedColumns = getCategorizedColumns;

        // Data service API
        this.DS_FILTER = grid.meta.dataService.DS_FILTER;
        this.reload = grid.meta.dataService.reload;
        this.loadData = grid.meta.dataService.loadData;
        this.loadMetaData = grid.meta.dataService.loadMetaData;
        this.setBreakdown = grid.meta.dataService.setBreakdown;
        this.getBreakdown = grid.meta.dataService.getBreakdown;
        this.getBreakdownLevel = grid.meta.dataService.getBreakdownLevel;
        this.setOrder = grid.meta.dataService.setOrder;
        this.getOrder = grid.meta.dataService.getOrder;
        this.setFilter = grid.meta.dataService.setFilter;
        this.getFilter = grid.meta.dataService.getFilter;
        this.updateData = grid.meta.dataService.updateData;

        // Selection service API
        this.isSelectionEmpty = grid.meta.selectionService.isSelectionEmpty;
        this.getSelection = grid.meta.selectionService.getSelection;
        this.clearSelection = grid.meta.selectionService.clearSelection;
        this.setSelection = grid.meta.selectionService.setSelection;
        this.setSelectionFilter = grid.meta.selectionService.setFilter;
        this.getSelectionOptions = grid.meta.selectionService.getConfig;
        this.setSelectionOptions = grid.meta.selectionService.setConfig;

        // Columns service API
        this.getVisibleColumns = grid.meta.columnsService.getVisibleColumns;
        this.setVisibleColumns = grid.meta.columnsService.setVisibleColumns;
        this.getColumnsToToggle = grid.meta.columnsService.getColumnsToToggle;
        this.findColumnInCategories =
            grid.meta.columnsService.findColumnInCategories;
        this.getTogglableColumns = grid.meta.columnsService.getTogglableColumns;

        this.refreshUI = refreshUI;

        // Listeners - pubsub rewiring
        this.onMetaDataUpdated = onMetaDataUpdated;
        this.onDataUpdated = onDataUpdated;
        this.onColumnsUpdated = onColumnsUpdated;
        this.onSelectionUpdated = onSelectionUpdated;

        function isInitialized() {
            return grid.meta.initialized;
        }

        function getMetaData() {
            return grid.meta.data;
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
                var inCategory = category.fields.indexOf(column.field) !== -1;
                if (!inCategory || !column.data.shown || column.data.permanent)
                    return false;
                if (
                    zemCostModeService.isTogglableCostMode(column.data.costMode)
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
                if (
                    newCategory.columns.length > 0 ||
                    newCategory.subcategories.length > 0
                ) {
                    categories.push(newCategory);
                }
            });
            return categories;
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
            registerListener(pubsub.EVENTS.METADATA_UPDATED, scope, callback);
        }

        function onDataUpdated(scope, callback) {
            registerListener(pubsub.EVENTS.DATA_UPDATED, scope, callback);
        }

        function onColumnsUpdated(scope, callback) {
            registerListener(
                pubsub.EVENTS.EXT_COLUMNS_UPDATED,
                scope,
                callback
            );
        }

        function onSelectionUpdated(scope, callback) {
            registerListener(
                pubsub.EVENTS.EXT_SELECTION_UPDATED,
                scope,
                callback
            );
        }

        function registerListener(event, scope, callback) {
            pubsub.register(event, scope, callback);
        }
    }

    return {
        createInstance: function(grid) {
            return new GridApi(grid);
        },
    };
});
