# `zemGrid` 

## `zemGridContainer` initialization

* `zemGridContainerTabsService` is used to create tabs for current level (ad group, campaign etc.) on init or entity changes
* tab is selected corresponding to current breakdown
    * this tab gets rendered in `zemGridContainer` template
* selected tab is activated if it wasn't activated before
    * `tab.gridIntegrationService` is set to a new instance of `zemGridIntegrationService`
    * `tab.gridIntegrationService.init()` is used to initialize grid in the tab
        * `tab.gridIntegrationService.grid` (private variable) is set to:
            ```plain
            grid = {
                api: undefined,
                options: <default_options>,
                dataSource: undefined,
            };
            ```
            Note: `<default_options>` currently only holds selection related options:
            ```plain
            {selection: {enabled, filtersEnabled, levels, callbacks: {isRowSelectable}}}
            ```
        * grid reload is set as an event handler for updates of date range (`zemDataFilterService.onDateRangeUpdate`), filter (`zemDataFilterService.onDataFilterUpdate`) and ad group updates (`zemAdGroupService.onEntityUpdated`)
            * reload sets correct filters on `grid.dataSource` (via `setGridDataSourceDateRangeAndFilters`) and loads data (via `grid.dataSource.loadData()`)
    * `tab.gridIntegrationService.configureDataSource` is used to create and configure `grid.dataSource`
        * `tab.gridIntegrationService` stores entity and breakdown internally
        * `tab.gridIntegrationService.createDataSource` adds new data source to `tab.gridIntegrationService`'s `DATA_SOURCE_CACHE` if datasource for tab's entity and breakdown doesn't exist
            * create metadata via `zemGridEndpointService.createMetaData(level, entityId, breakdown)`
            * create endpoint via `zemGridEndpointService.createEndpoint(metadata)`
            * create data source via `zemDataSourceService.createInstance(endpoint, $scope)` (`$scope` is used for pub-sub notification broadcasting in this instance of data source)
        * `grid.dataSource` is then set to data source created or data source loaded form `DATA_SOURCE_CACHE`
    * `tab.grid` is set to grid instance in `tab.gridIntegrationService`
* `zemGrid` is rendered inside `zemGridContainer`:
    * inputs: `tab.grid.dataSource`, `tab.grid.options`
    * outputs: `onInitialized`

## `zemGrid` initialization

* new `$ctrl.grid` object gets created in `zemGrid.$onInit()` (`$onInit` is always triggered when switching tabs) via `zemGridObject.createGrid()`
    * `$ctrl.grid: zemGridObject`
        * main data structure holding entire grid state that is passed to the grid components and services
        * `$ctrl.grid.meta.pubsub = zemGridPubSub.createInstance($scope)`
            * pub-sub service enabling communication between different grid's components and services
        * `$ctrl.grid.meta.dataService = zemGridDataService.createInstance($ctrl.grid, $ctrl.dataSource)`
            * a service (wrapper) responsible for requesting and parsing data (and metadata) correctly from tab's `$ctrl.dataSource`
            * listens to `dataSource.onStatsUpdated` and `dataSource.onDataUpdated` and acts accordingly
            * `dataService.replaceDataSource` should be used to swap data sources used by grids in different tabs, but it's not relevant, because grid `$onInit` is always executed when switching tabs (?)
        * `$ctrl.grid.meta.columnsService = zemGridColumnsService.createInstance($ctrl.grid)`
            * responsible for calculating which columns are visible in grid
            * different events trigger recalculation of visible columns:
                * `EVENTS.METADATA_UPDATED` and `EVENTS.DATA_UPDATED`
                * `zemCostModeService.onCostModeUpdate`
                * `zemNavigationNewService.onUsesBCMv2Update`
                * `zemNavigationNewService.onHierarchyUpdate`
            * exposes methods to get/set columns visibility
        * `$ctrl.grid.meta.orderService = zemGridOrderService.createInstance($ctrl.grid)`
            * synchronizes `grid.meta.dataService` order and order indicator in `zemGridHeaderCellData`
        * `$ctrl.grid.meta.collapseService = zemGridCollapseService.createInstance($ctrl.grid)`
            * manages visibility of grid's rows - `zemGridCellBreakdownField` collapse/expand row toggle
        * `$ctrl.grid.meta.selectionService = zemGridSelectionService.createInstance($ctrl.grid)`
            * provides selection functionality used by checkbox directives (header and cell)
        * `$ctrl.grid.meta.api = zemGridApi.createInstance($ctrl.grid)`
            * `zemGridApi` provides interface for interaction with `zemGrid` - reference can be sent to non-grid components (e.g. `zemGridColumnSelector`, `zemGridBreakdownSelector` etc.)
* `onInitialized` output is used to set grid api via `tab.gridIntegrationService.setGridApi(gridApi`) once `zemGrid` is initialized
