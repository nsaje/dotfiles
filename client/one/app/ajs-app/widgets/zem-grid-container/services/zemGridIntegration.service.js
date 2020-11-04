var Level = require('../../../../app.constants').Level;
var Breakdown = require('../../../../app.constants').Breakdown;

angular
    .module('one.widgets')
    .factory('zemGridIntegrationService', function(
        zemAuthStore,
        zemGridConstants,
        zemGridEndpointService,
        zemDataSourceService,
        zemDataFilterService,
        zemSelectionService,
        zemGridIntegrationSelectionService,
        zemEntitiesUpdatesService
    ) {
        // eslint-disable-line

        function IntegrationService($scope) {
            var entity;
            var level;
            var breakdown;
            var grid;

            this.initialize = initialize;
            this.configureRenderingEngine = configureRenderingEngine;
            this.configureDataSource = configureDataSource;
            this.getGrid = getGrid;
            this.setGridApi = setGridApi;

            function initialize(_entity, _level, _breakdown) {
                entity = _entity;
                level = _level;
                breakdown = _breakdown;

                initializeGrid();

                var onDateRangeUpdateHandler = zemDataFilterService.onDateRangeUpdate(
                    reload
                );
                var onDataFilterUpdateHandler = zemDataFilterService.onDataFilterUpdate(
                    reload
                );
                $scope.$on('$destroy', onDateRangeUpdateHandler);
                $scope.$on('$destroy', onDataFilterUpdateHandler);

                var entitiesUpdates$ = zemEntitiesUpdatesService
                    .getAllUpdates$()
                    .subscribe(function(entityUpdate) {
                        if (
                            entityUpdate.action === constants.entityAction.EDIT
                        ) {
                            reload();
                        }
                    });
                $scope.$on('$destroy', function() {
                    entitiesUpdates$.unsubscribe();
                });
            }

            function configureRenderingEngine() {
                grid.renderingEngine = getGridRenderingEngine(level, breakdown);
            }

            function configureDataSource() {
                var replaceRows =
                    grid.renderingEngine ===
                    zemGridConstants.gridRenderingEngineType.SMART_GRID;
                grid.dataSource = createDataSource(
                    entity,
                    level,
                    breakdown,
                    replaceRows
                );
                setGridDataSourceDateRangeAndFilters();
            }

            function setGridApi(api) {
                grid.api = api;
                initializeSelectionBind();
            }

            function getGrid() {
                return grid;
            }

            //
            // PRIVATE
            //

            function initializeGrid() {
                grid = {
                    api: undefined,
                    options: createDefaultGridOptions(),
                    dataSource: undefined,
                    renderingEngine: undefined,
                };
            }

            function createDataSource(entity, level, breakdown, replaceRows) {
                var id = entity ? entity.id : null;
                var metadata = zemGridEndpointService.createMetaData(
                    level,
                    id,
                    breakdown
                );
                var endpoint = zemGridEndpointService.createEndpoint(metadata);
                var dataSource = zemDataSourceService.createInstance(
                    endpoint,
                    $scope,
                    replaceRows
                );
                return dataSource;
            }

            function createDefaultGridOptions() {
                var options = {
                    selection: {
                        enabled: true,
                        filtersEnabled: true,
                        levels: [0, 1],
                    },
                };
                return options;
            }

            function reload() {
                setGridDataSourceDateRangeAndFilters();
                grid.api.loadData();
            }

            function setGridDataSourceDateRangeAndFilters() {
                var dateRange = zemDataFilterService.getDateRange();
                grid.dataSource.setDateRange(dateRange);

                var FILTER = grid.dataSource.FILTER;
                var showArchived = zemDataFilterService.getShowArchived();
                var filteredSources = zemDataFilterService.getFilteredSources();
                var filteredAgencies = zemDataFilterService.getFilteredAgencies();
                var filteredAccountTypes = zemDataFilterService.getFilteredAccountTypes();
                var filteredBusinesses = zemDataFilterService.getFilteredBusinesses();
                var filteredPublisherStatus = zemDataFilterService.getFilteredPublisherStatus();

                grid.dataSource.setFilter(
                    FILTER.FILTERED_MEDIA_SOURCES,
                    filteredSources
                );
                grid.dataSource.setFilter(
                    FILTER.SHOW_ARCHIVED_SOURCES,
                    showArchived
                );

                if (!entity) {
                    grid.dataSource.setFilter(
                        FILTER.FILTERED_AGENCIES,
                        filteredAgencies
                    );
                    grid.dataSource.setFilter(
                        FILTER.FILTERED_ACCOUNT_TYPES,
                        filteredAccountTypes
                    );
                    grid.dataSource.setFilter(
                        FILTER.FILTERED_BUSINESSES,
                        filteredBusinesses
                    );
                }

                if (
                    breakdown === constants.breakdown.PUBLISHER ||
                    breakdown === constants.breakdown.PLACEMENT
                ) {
                    grid.dataSource.setFilter(
                        FILTER.SHOW_BLACKLISTED_PUBLISHERS,
                        filteredPublisherStatus
                    );
                }
            }

            function initializeSelectionBind() {
                var initialized = false;
                var canUpdateSelection = true;

                if (onSelectionUpdateHandler) onSelectionUpdateHandler();
                var onSelectionUpdateHandler = zemSelectionService.onSelectionUpdate(
                    function() {
                        canUpdateSelection = false;
                        loadSelection();
                        canUpdateSelection = true;
                    }
                );
                $scope.$on('$destroy', onSelectionUpdateHandler);

                if (onDataUpdatedHandler) onDataUpdatedHandler();
                var onDataUpdatedHandler = grid.api.onDataUpdated(
                    $scope,
                    function() {
                        if (initialized) return;
                        initialized = true;
                        loadSelection();
                    }
                );
                $scope.$on('$destroy', onDataUpdatedHandler);

                if (onSelectionUpdatedHandler) onSelectionUpdatedHandler();
                var onSelectionUpdatedHandler = grid.api.onSelectionUpdated(
                    $scope,
                    function() {
                        if (canUpdateSelection) {
                            updateSelection();
                        }
                    }
                );
                $scope.$on('$destroy', onSelectionUpdatedHandler);
            }

            function loadSelection() {
                var selection = zemGridIntegrationSelectionService.createGridSelection(
                    grid.api
                );
                grid.api.setSelection(selection);
            }

            function updateSelection() {
                // Daily stats placement query takes too long so the selection
                // should not be synchronized with zemSelectionService
                if (breakdown === constants.breakdown.PLACEMENT) return;

                var selection = zemGridIntegrationSelectionService.createCoreSelection(
                    grid.api
                );
                zemSelectionService.setSelection(selection);
            }

            var smartGridSupportedLevels = [
                Level.ALL_ACCOUNTS,
                Level.ACCOUNTS,
                Level.CAMPAIGNS,
                Level.AD_GROUPS,
            ];
            var smartGridSupportedBreakdowns = [
                Breakdown.ACCOUNT,
                Breakdown.CAMPAIGN,
                Breakdown.AD_GROUP,
                Breakdown.CONTENT_AD,
                Breakdown.PUBLISHER,
                Breakdown.PLACEMENT,
                Breakdown.MEDIA_SOURCE,
                Breakdown.COUNTRY,
                Breakdown.STATE,
                Breakdown.DMA,
                Breakdown.DEVICE,
                Breakdown.ENVIRONMENT,
                Breakdown.OPERATING_SYSTEM,
                Breakdown.BROWSER,
                Breakdown.CONNECTION_TYPE,
            ];

            function getGridRenderingEngine(level, breakdown) {
                if (
                    zemAuthStore.hasPermission(
                        'zemauth.can_use_smart_grid_in_analytics_view'
                    ) &&
                    smartGridSupportedLevels.includes(level) &&
                    smartGridSupportedBreakdowns.includes(breakdown)
                ) {
                    return zemGridConstants.gridRenderingEngineType.SMART_GRID;
                }
                return zemGridConstants.gridRenderingEngineType.CUSTOM_GRID;
            }
        }

        return {
            createInstance: function($scope) {
                return new IntegrationService($scope);
            },
        };
    });
