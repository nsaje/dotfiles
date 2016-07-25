/* globals oneApp */

oneApp.controller('DevelopmentCtrl', ['$scope', '$state', function ($scope, $state) {
    $scope.$on('$stateChangeSuccess', function () {
        if ($state.is('main.development.grid')
            && !$scope.hasPermission('zemauth.can_access_table_breakdowns_feature')) {
            $state.go('main');
        }
    });
}]);

oneApp.controller('DevelopmentGridCtrl', ['$scope', '$timeout', 'zemGridConstants', 'zemDataSourceService', 'zemGridDebugEndpoint', function ($scope, $timeout, zemGridConstants, zemDataSourceService, zemGridDebugEndpoint) { // eslint-disable-line max-len
    var dataSource = zemDataSourceService.createInstance(zemGridDebugEndpoint.createEndpoint());

    var options = {
        enableSelection: true,
        enableTotalsSelection: true,
        maxSelectedRows: 3,

        selection: {
            enabled: true,
            filtersEnabled: true,
            levels: [0, 1],
            customFilters: [
                {
                    type: zemGridConstants.gridSelectionCustomFilterType.LIST,
                    name: 'Account manager (list)',
                    filters: [
                        {
                            name: 'Tadej',
                            callback: selectionFilter('Tadej'),
                        },
                        {
                            name: 'Helen',
                            callback: selectionFilter('Helen'),
                        }
                    ]
                },
                {
                    type: zemGridConstants.gridSelectionCustomFilterType.ITEM,
                    filter: {
                        name: 'Account Manager (item) - Ana',
                        callback: selectionFilter('Ana'),
                    }
                }
            ],
        }
    };

    function selectionFilter (value) {
        return function (row) {
            var accountManager = row.data.stats['default_account_manager'];
            if (!accountManager || !accountManager.value) return false;
            return accountManager.value.startsWith(value);
        };
    }

    // GridApi is defined by zem-grid in initialization, therefor
    // it will be available in the next cycle; postpone initialization using $timeout
    $scope.grid = {
        api: undefined,
        options: options,
        dataSource: dataSource,
    };

    $scope.$watch('grid.api', function (newValue, oldValue) {
        if (newValue === oldValue) return; // Equal when watch is initialized (AngularJS docs)
        initializeGridApi();
    });

    function initializeGridApi () {
        // Initialize GridApi listeners
        $scope.grid.api.onSelectionUpdated($scope, function () {
            console.log($scope.grid.api.getSelection()); // eslint-disable-line
        });
    }
}]);

