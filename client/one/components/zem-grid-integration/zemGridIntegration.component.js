/* globals angular, constants */
'use strict';

angular.module('one.legacy').directive('zemGridIntegration', [function () { // eslint-disable-line max-len
    return {
        restrict: 'E',
        replace: false,
        scope: {},
        templateUrl: '/components/zem-grid-integration/zemGridIntegration.component.html',
        bindToController: {
            api: '=api',
            options: '=options',

            level: '=level',
            breakdown: '=breakdown',
            entityId: '=entityId',

            selection: '=',
            selectionCallback: '=',

            hasPermission: '=zemHasPermission',
            isPermissionInternal: '=zemIsPermissionInternal',
        },
        controllerAs: 'ctrl',
        controller: 'ZemGridIntegrationCtrl',
    };
}]);

angular.module('one.legacy').controller('ZemGridIntegrationCtrl', ['$scope', '$timeout', '$state', 'zemGridEndpointService', 'zemDataSourceService', 'zemFilterService', function ($scope, $timeout, $state, zemGridEndpointService, zemDataSourceService, zemFilterService) {
    var vm = this;
    $scope.hasPermission = this.hasPermission;
    $scope.isPermissionInternal = this.isPermissionInternal;

    vm.grid = undefined;

    initialize();

    function initialize () {
        initializeGrid();
        initializeFilterWatches();
        loadState();

        $scope.$watch('ctrl.grid.api', function (newValue, oldValue) {
            if (newValue === oldValue) return; // Equal when watch is initialized (AngularJS docs)

            // pass api back to host controller
            vm.api = vm.grid.api;
            if (vm.selection) initializeSelectionBind();
        });
    }

    function initializeGrid () {
        vm.grid = {
            api: undefined,
            options: vm.options || createDefaultGridOptions(),
            dataSource: createDataSource(),
        };
    }

    function createDataSource () {
        var metadata = zemGridEndpointService.createMetaData($scope, vm.level, vm.entityId, vm.breakdown);
        var endpoint = zemGridEndpointService.createEndpoint(metadata);
        var dataSource = zemDataSourceService.createInstance(endpoint, $scope);
        return dataSource;
    }

    function createDefaultGridOptions () {
        return {
            selection: {
                enabled: true,
                levels: [0, 1],
                callbacks: {
                    isRowSelectable: function () {
                        // Allow at most 4 rows to be selected
                        return vm.api.getSelection().selected.length < 4;
                    }
                }
            }
        };
    }

    function loadState () {
        loadFilters();
    }

    function loadFilters () {
        var FILTER = vm.grid.dataSource.FILTER;

        vm.grid.dataSource.setFilter(FILTER.FILTERED_MEDIA_SOURCES, zemFilterService.getFilteredSources());
        vm.grid.dataSource.setFilter(FILTER.SHOW_ARCHIVED_SOURCES, zemFilterService.getShowArchived());

        if (vm.level === constants.level.ALL_ACCOUNTS) {
            vm.grid.dataSource.setFilter(FILTER.FILTERED_AGENCIES, zemFilterService.getFilteredAgencies());
            vm.grid.dataSource.setFilter(FILTER.FILTERED_ACCOUNT_TYPES, zemFilterService.getFilteredAccountTypes());
        }

        if (vm.breakdown === constants.breakdown.PUBLISHER) {
            vm.grid.dataSource.setFilter(FILTER.SHOW_BLACKLISTED_PUBLISHERS, zemFilterService.getBlacklistedPublishers());
        }
    }

    function initializeFilterWatches () {
        function filterWatch (newValue, oldValue) {
            if (newValue === oldValue) return;
            loadFilters();
            vm.grid.dataSource.getData();
        }

        $scope.$watchCollection(zemFilterService.getFilteredAgencies, filterWatch);
        $scope.$watchCollection(zemFilterService.getFilteredAccountTypes, filterWatch);
        $scope.$watchCollection(zemFilterService.getFilteredSources, filterWatch);
        $scope.$watch(zemFilterService.getShowArchived, filterWatch);
        $scope.$watch(zemFilterService.getBlacklistedPublishers, filterWatch);
    }

    function initializeSelectionBind () {
        var initialized = false;
        var canUpdateSelection = true;

        vm.grid.api.onDataUpdated($scope, function () {
            if (initialized) return;
            initialized = true;

            loadSelection();

            $scope.$watch('ctrl.selection', function (newValue, oldValue) {
                if (newValue === oldValue) return; // Equal when watch is initialized (AngularJS docs)
                canUpdateSelection = false;
                loadSelection();
                canUpdateSelection = true;
            }, true);

            vm.grid.api.onSelectionUpdated($scope, function () {
                if (canUpdateSelection) updateSelection();
            });
        });
    }

    function loadSelection () {
        var selection = vm.grid.api.getSelection();
        var rows = vm.grid.api.getRows();
        selection.selected = [];
        rows.forEach(function (row) {
            if (row.level === 0 && vm.selection.totals) {
                selection.selected.push(row);
            }
            if (row.level === 1 && vm.selection.entityIds.indexOf(row.data.breakdownId) >= 0) {
                selection.selected.push(row);
            }
        });
        vm.grid.api.setSelection(selection);
    }

    function updateSelection () {
        var selectedRows = vm.grid.api.getSelection().selected;
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

        if (!angular.equals(selection, vm.selection)) {
            angular.extend(vm.selection, selection);
            vm.selectionCallback();
        }
    }
}]);

