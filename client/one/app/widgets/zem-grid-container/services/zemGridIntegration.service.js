angular.module('one.widgets').factory('zemGridIntegrationService', function ($timeout, zemPermissions, zemGridConstants, zemGridEndpointService, zemDataSourceService, zemDataFilterService, zemSelectionService, zemAdGroupService, zemGridIntegrationSelectionService) { // eslint-disable-line

    function IntegrationService (entity, $scope) {
        var DATA_SOURCE_CACHE = {};

        var breakdown;
        var grid;

        this.initialize = initialize;
        this.setBreakdown = setBreakdown;
        this.getGrid = getGrid;
        this.setGridApi = setGridApi;

        function initialize () {
            initializeGrid();

            var onDateRangeUpdateHandler = zemDataFilterService.onDateRangeUpdate(reload);
            var onDataFilterUpdateHandler = zemDataFilterService.onDataFilterUpdate(reload);
            $scope.$on('$destroy', onDateRangeUpdateHandler);
            $scope.$on('$destroy', onDataFilterUpdateHandler);

            // TODO: Check this out - Why only AdGroupService
            // Fixed grid not refreshing after settings are saved in side panel.
            var onEntityUpdatedHandler = zemAdGroupService.onEntityUpdated(reload);
            $scope.$on('$destroy', onEntityUpdatedHandler);
        }

        function setBreakdown (_breakdown) {
            breakdown = _breakdown;
            grid.dataSource = createDataSource(breakdown);
            loadState();
        }

        function setGridApi (api) {
            grid.api = api;
            $timeout(initializeSelectionBind);
        }

        function getGrid () {
            return grid;
        }

        function initializeGrid () {
            grid = {
                api: undefined,
                options: createDefaultGridOptions(),
                dataSource: undefined
            };
        }

        function createDataSource (breakdown) {
            if (!DATA_SOURCE_CACHE[breakdown]) {
                var metadata = zemGridEndpointService.createMetaData(entity.level, entity.id, breakdown);
                var endpoint = zemGridEndpointService.createEndpoint(metadata);
                var dataSource = zemDataSourceService.createInstance(endpoint, $scope);
                DATA_SOURCE_CACHE[breakdown] = dataSource;
            }

            return DATA_SOURCE_CACHE[breakdown];
        }

        function createDefaultGridOptions () {
            var options = {
                selection: {
                    enabled: true,
                    filtersEnabled: true,
                    levels: [0, 1],
                }
            };

            // TODO: Check for cleaner solution
            if (!zemPermissions.hasPermission('zemauth.bulk_actions_on_all_levels')) {
                options.selection.callbacks = {
                    isRowSelectable: function (row) {
                        if (row.level === zemGridConstants.gridRowLevel.FOOTER) return true;

                        // Allow at most 4 data rows to be selected
                        var maxSelectedRows = 4;
                        if (zemSelectionService.isTotalsSelected()) {
                            maxSelectedRows = 5;
                        }
                        return grid.api.getSelection().selected.length < maxSelectedRows;
                    }
                };
            }

            return options;
        }

        function reload () {
            loadState();
            grid.dataSource.loadData();
        }

        function loadState () {
            loadDataFilter();
        }

        function loadDataFilter () {
            var dateRange = zemDataFilterService.getDateRange();
            grid.dataSource.setDateRange(dateRange);

            var FILTER = grid.dataSource.FILTER;
            var showArchived = zemDataFilterService.getShowArchived();
            var filteredSources = zemDataFilterService.getFilteredSources();
            var filteredAgencies = zemDataFilterService.getFilteredAgencies();
            var filteredAccountTypes = zemDataFilterService.getFilteredAccountTypes();
            var filteredPublisherStatus = zemDataFilterService.getFilteredPublisherStatus();

            grid.dataSource.setFilter(FILTER.FILTERED_MEDIA_SOURCES, filteredSources);
            grid.dataSource.setFilter(FILTER.SHOW_ARCHIVED_SOURCES, showArchived);

            if (entity.level === constants.level.ALL_ACCOUNTS) {
                grid.dataSource.setFilter(FILTER.FILTERED_AGENCIES, filteredAgencies);
                grid.dataSource.setFilter(FILTER.FILTERED_ACCOUNT_TYPES, filteredAccountTypes);
            }

            if (breakdown === constants.breakdown.PUBLISHER) {
                grid.dataSource.setFilter(FILTER.SHOW_BLACKLISTED_PUBLISHERS, filteredPublisherStatus);
            }
        }

        function initializeSelectionBind () {
            var initialized = false;
            var canUpdateSelection = true;

            var onSelectionUpdateHandler = zemSelectionService.onSelectionUpdate(function () {
                canUpdateSelection = false;
                loadSelection();
                canUpdateSelection = true;
            });
            $scope.$on('$destroy', onSelectionUpdateHandler);

            grid.api.onDataUpdated($scope, function () {
                if (initialized) return;
                initialized = true;

                loadSelection();

                grid.api.onSelectionUpdated($scope, function () {
                    if (canUpdateSelection) updateSelection();
                });
            });
        }

        function loadSelection () {
            var selection = zemGridIntegrationSelectionService.createGridSelection(grid.api);
            grid.api.setSelection(selection);
        }

        function updateSelection () {
            // Publisher selection is needed only internally and should not be synchronized with zemSelectionService
            if (breakdown === constants.breakdown.PUBLISHER) return;

            var selection = zemGridIntegrationSelectionService.createCoreSelection(grid.api);
            zemSelectionService.setSelection(selection);
        }
    }

    return {
        createInstance: function (entity, $scope) {
            return new IntegrationService(entity, $scope);
        }

    };
});
