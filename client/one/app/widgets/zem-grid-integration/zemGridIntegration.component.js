/* globals angular, constants */

angular.module('one.widgets').component('zemGridIntegration', {
    bindings: {
        api: '=api',
        options: '=options',

        level: '=level',
        breakdown: '=breakdown',
        entityId: '=entityId',
    },
    templateUrl: '/app/widgets/zem-grid-integration/zemGridIntegration.component.html',
    controller: function ($scope, $timeout, $state, zemGridEndpointService, zemDataSourceService, zemDataFilterService, zemPermissions, zemGridIntegrationSelectionService, zemGridConstants, zemSelectionService) { // eslint-disable-line max-len
        var $ctrl = this;
        var dataFilterUpdateHandler;
        var selectionUpdateHandler;
        var canUpdateSelection = true;

        $ctrl.grid = undefined;

        $ctrl.$onInit = function () {
            initializeGrid();
            initializeFilterWatches();
            loadState();

            selectionUpdateHandler = zemSelectionService.onSelectionUpdate(function () {
                canUpdateSelection = false;
                loadSelection();
                canUpdateSelection = true;
            });

            $scope.$watch('$ctrl.grid.api', function (newValue, oldValue) {
                if (newValue === oldValue) return; // Equal when watch is initialized (AngularJS docs)

                // pass api back to host controller
                $ctrl.api = $ctrl.grid.api;
                initializeSelectionBind();
            });
        };

        $ctrl.$onDestroy = function () {
            if (dataFilterUpdateHandler) dataFilterUpdateHandler();
            if (selectionUpdateHandler) selectionUpdateHandler();
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
                    isRowSelectable: function (row) {
                        if (row.level === zemGridConstants.gridRowLevel.FOOTER) return true;

                        // Allow at most 4 data rows to be selected
                        var maxSelectedRows = 4;
                        if (zemSelectionService.isTotalsSelected()) {
                            maxSelectedRows = 5;
                        }
                        return $ctrl.api.getSelection().selected.length < maxSelectedRows;
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

            $ctrl.grid.api.onDataUpdated($scope, function () {
                if (initialized) return;
                initialized = true;

                loadSelection();

                $ctrl.grid.api.onSelectionUpdated($scope, function () {
                    if (canUpdateSelection) updateSelection();
                });
            });
        }

        function loadSelection () {
            var selection = zemGridIntegrationSelectionService.createGridSelection($ctrl.grid.api);
            $ctrl.grid.api.setSelection(selection);
        }

        function updateSelection () {
            // Publisher selection is needed only internally and should not be synchronized with zemSelectionService
            if ($ctrl.breakdown === constants.breakdown.PUBLISHER) return;

            var selection = zemGridIntegrationSelectionService.createCoreSelection($ctrl.grid.api);
            zemSelectionService.setSelection(selection);
        }
    }
});

