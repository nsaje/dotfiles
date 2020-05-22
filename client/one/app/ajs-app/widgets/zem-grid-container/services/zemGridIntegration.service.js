angular
    .module('one.widgets')
    .factory('zemGridIntegrationService', function(
        $timeout,
        zemPermissions,
        zemGridConstants,
        zemGridEndpointService,
        zemDataSourceService,
        zemDataFilterService,
        zemSelectionService,
        zemAdGroupService,
        zemGridIntegrationSelectionService,
        zemEntitiesUpdatesService
    ) {
        // eslint-disable-line

        function IntegrationService($scope) {
            var DATA_SOURCE_CACHE = {};

            var breakdown;
            var entity;
            var grid;

            this.initialize = initialize;
            this.configureDataSource = configureDataSource;
            this.getGrid = getGrid;
            this.setGridApi = setGridApi;

            function initialize() {
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

            function configureDataSource(_entity, _breakdown) {
                breakdown = _breakdown;
                entity = _entity;
                grid.dataSource = createDataSource(entity, breakdown);
                setGridDataSourceDateRangeAndFilters();
            }

            function setGridApi(api) {
                grid.api = api;
                initializeSelectionBind();
            }

            function getGrid() {
                return grid;
            }

            function initializeGrid() {
                grid = {
                    api: undefined,
                    options: createDefaultGridOptions(),
                    dataSource: undefined,
                };
            }

            function createDataSource(entity, breakdown) {
                function createKey(entity, breakdown) {
                    if (!entity) {
                        return 'all_accounts-' + breakdown;
                    }
                    return '{type}-{id}-{breakdown}'
                        .replace('{type}', entity.type)
                        .replace('{id}', entity.id)
                        .replace('{breakdown}', breakdown);
                }

                var key = createKey(entity, breakdown);

                if (!DATA_SOURCE_CACHE[key]) {
                    var id = entity ? entity.id : null;
                    var level = entity
                        ? constants.entityTypeToLevelMap[entity.type]
                        : constants.level.ALL_ACCOUNTS;
                    var metadata = zemGridEndpointService.createMetaData(
                        level,
                        id,
                        breakdown
                    );
                    var endpoint = zemGridEndpointService.createEndpoint(
                        metadata
                    );
                    var dataSource = zemDataSourceService.createInstance(
                        endpoint,
                        $scope
                    );
                    DATA_SOURCE_CACHE[key] = dataSource;
                }

                return DATA_SOURCE_CACHE[key];
            }

            function createDefaultGridOptions() {
                var options = {
                    selection: {
                        enabled: true,
                        filtersEnabled: true,
                        levels: [0, 1],
                    },
                };

                // TODO: Check for cleaner solution
                if (
                    !zemPermissions.hasPermission(
                        'zemauth.bulk_actions_on_all_levels'
                    )
                ) {
                    options.selection.callbacks = {
                        isRowSelectable: function(row) {
                            if (
                                row.level ===
                                zemGridConstants.gridRowLevel.FOOTER
                            )
                                return true;

                            // Allow at most 4 data rows to be selected
                            var maxSelectedRows = 4;
                            if (zemSelectionService.isTotalsSelected()) {
                                maxSelectedRows = 5;
                            }
                            return (
                                grid.api.getSelection().selected.length <
                                maxSelectedRows
                            );
                        },
                    };
                }

                return options;
            }

            function reload() {
                setGridDataSourceDateRangeAndFilters();
                grid.dataSource.loadData();
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

                var onSelectionUpdateHandler = zemSelectionService.onSelectionUpdate(
                    function() {
                        canUpdateSelection = false;
                        loadSelection();
                        canUpdateSelection = true;
                    }
                );
                $scope.$on('$destroy', onSelectionUpdateHandler);

                grid.api.onDataUpdated($scope, function() {
                    if (initialized) return;
                    initialized = true;

                    loadSelection();

                    grid.api.onSelectionUpdated($scope, function() {
                        if (canUpdateSelection) updateSelection();
                    });
                });
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
        }

        return {
            createInstance: function($scope) {
                return new IntegrationService($scope);
            },
        };
    });
