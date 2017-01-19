/* globals angular, constants */

angular.module('one.widgets').component('zemGridIntegration', {
    bindings: {
        api: '=api',
        options: '=options',

        level: '=level',
        breakdown: '=breakdown',
        entityId: '=entityId',

        selection: '=',
        selectionCallback: '=',
    },
    templateUrl: '/app/widgets/zem-grid-integration/zemGridIntegration.component.html',
    controller: function ($scope, $timeout, $state, zemGridEndpointService, zemDataSourceService, zemDataFilterService, zemPermissions) {
        var dataFilterUpdateHandler;
        var $ctrl = this;

        $ctrl.grid = undefined;

        $ctrl.$onInit = function () {
            initializeGrid();
            initializeFilterWatches();
            loadState();

            $scope.$watch('$ctrl.grid.api', function (newValue, oldValue) {
                if (newValue === oldValue) return; // Equal when watch is initialized (AngularJS docs)

                // pass api back to host controller
                $ctrl.api = $ctrl.grid.api;
                if ($ctrl.selection) initializeSelectionBind();
            });
        };

        $ctrl.$onDestroy = function () {
            if (dataFilterUpdateHandler) dataFilterUpdateHandler();
        };

        function initializeGrid () {
            $ctrl.grid = {
                api: undefined,
                options: $ctrl.options || createDefaultGridOptions(),
                dataSource: createDataSource(),
            };
        }

        function createDataSource () {
            var metadata = zemGridEndpointService.createMetaData($ctrl.level, $ctrl.entityId, $ctrl.breakdown);
            var endpoint = zemGridEndpointService.createEndpoint(metadata);
            var dataSource = zemDataSourceService.createInstance(endpoint, $scope);
            return dataSource;
        }

        function createDefaultGridOptions () {
            var options = {
                selection: {
                    enabled: true,
                    filtersEnabled: true,
                    levels: [0, 1],
                }
            };
            if (!zemPermissions.hasPermission('zemauth.bulk_actions_on_all_levels')) {
                options.selection.callbacks = {
                    isRowSelectable: function () {
                        // Allow at most 4 rows to be selected
                        return $ctrl.api.getSelection().selected.length < 4;
                    }
                };
            }
            return options;
        }

        function loadState () {
            loadFilters();
        }

        function loadFilters () {
            var FILTER = $ctrl.grid.dataSource.FILTER;

            var showArchived = zemDataFilterService.getShowArchived();
            var filteredSources = zemDataFilterService.getFilteredSources();
            var filteredAgencies = zemDataFilterService.getFilteredAgencies();
            var filteredAccountTypes = zemDataFilterService.getFilteredAccountTypes();
            var filteredPublisherStatus = zemDataFilterService.getFilteredPublisherStatus();

            $ctrl.grid.dataSource.setFilter(FILTER.FILTERED_MEDIA_SOURCES, filteredSources);
            $ctrl.grid.dataSource.setFilter(FILTER.SHOW_ARCHIVED_SOURCES, showArchived);

            if ($ctrl.level === constants.level.ALL_ACCOUNTS) {
                $ctrl.grid.dataSource.setFilter(FILTER.FILTERED_AGENCIES, filteredAgencies);
                $ctrl.grid.dataSource.setFilter(FILTER.FILTERED_ACCOUNT_TYPES, filteredAccountTypes);
            }

            if ($ctrl.breakdown === constants.breakdown.PUBLISHER) {
                $ctrl.grid.dataSource.setFilter(FILTER.SHOW_BLACKLISTED_PUBLISHERS, filteredPublisherStatus);
            }
        }

        function initializeFilterWatches () {
            function filterWatch (newValue, oldValue) {
                if (newValue === oldValue) return;
                loadFilters();
                $ctrl.grid.dataSource.getData();
            }

            dataFilterUpdateHandler = zemDataFilterService.onDataFilterUpdate(filterWatch);
        }

        function initializeSelectionBind () {
            var initialized = false;
            var canUpdateSelection = true;

            $ctrl.grid.api.onDataUpdated($scope, function () {
                if (initialized) return;
                initialized = true;

                loadSelection();

                $scope.$watch('$ctrl.selection', function (newValue, oldValue) {
                    if (newValue === oldValue) return; // Equal when watch is initialized (AngularJS docs)
                    canUpdateSelection = false;
                    loadSelection();
                    canUpdateSelection = true;
                }, true);

                $ctrl.grid.api.onSelectionUpdated($scope, function () {
                    if (canUpdateSelection) updateSelection();
                });
            });
        }

        function loadSelection () {
            var selection = $ctrl.grid.api.getSelection();
            var rows = $ctrl.grid.api.getRows();
            selection.selected = [];
            rows.forEach(function (row) {
                if (row.level === 0 && $ctrl.selection.totals) {
                    selection.selected.push(row);
                }
                if (row.level === 1 && $ctrl.selection.entityIds.indexOf(row.data.breakdownId) >= 0) {
                    selection.selected.push(row);
                }
            });
            $ctrl.grid.api.setSelection(selection);
        }

        function updateSelection () {
            var selectedRows = $ctrl.grid.api.getSelection().selected;
            var selection = {
                totals: false,
                entityIds: [],
            };

            selectedRows.forEach(function (row) {
                if (row.level === 0) {
                    selection.totals = true;
                }
                if (row.level === 1) {
                    selection.entityIds.push(row.data.breakdownId);
                }
            });

            if (!angular.equals(selection, $ctrl.selection)) {
                angular.extend($ctrl.selection, selection);
                $ctrl.selectionCallback();
            }
        }
    }
});

