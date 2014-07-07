oneActionLogApp.controller('ActionLogCtrl', ['$scope', '$state', '$location', 'api', function ($scope, $state, $location, api) {

    $scope.user = null;
    $scope.actionLogItems = null;

    $scope.filterItems = {};
    $scope.filterSelected = {};

    $scope.updateFilter = function (filter, choice) {
        $scope.dropdownIsOpen = false;
        $scope.filterSelected[filter] = choice;
        updateActionLog();
    }

    var updateActionLog = function () {
        var args_filters = {};
        angular.forEach($scope.filterSelected, function (value, filter) {
            if (value[0] != 0) {
                args_filters[filter] = value[0];
            }
        });

        api.actionLog.list(args_filters).then(function (data) {
            $scope.actionLogItems = data.actionLogItems;

            angular.forEach(data.filters, function (items, filter) {
                if (!$scope.filterSelected[filter]) {
                    $scope.filterSelected[filter] = items[0];
                }
            });
            $scope.filterItems = data.filters;
        });
    };

    updateActionLog();

}]);
