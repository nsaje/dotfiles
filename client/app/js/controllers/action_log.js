oneActionLogApp.controller('ActionLogCtrl', ['$scope', '$state', '$location', 'api', function ($scope, $state, $location, api) {

    $scope.user = null;
    $scope.actionLogItems = null;

    $scope.filters = {
        items: {},

        selected: {},

        defaults: {
            'state': 1
        },

        getFilterByKey: function (filter, key) {
            if (!$scope.filters.items[filter]) {
                return;
            }

            var found = $scope.filters.items[filter].filter(function (v) {
                return v[0] === key;
            });

            if (found.length > 0) {
                return found[0];
            }

            return null;
        },

        updateSearchFilters: function () {
            var str_filters = $.map($scope.filters.selected, function (v, k) {
                return [k, v[0]].join(':');
            });

            $location.search({
                filters: str_filters
            });
        },

        getSearchFilters: function () {
            var filter_str = $location.search().filters;

            if (!filter_str) {
                filter_str = [];
            } else if (!(filter_str instanceof Array)) {
                filter_str = [filter_str];
            }

            var filters_dict = {};

            filter_str.map(function (v) {
                var kv = v.split(':');
                if (kv.length !== 2) {
                    return;
                }
                filters_dict[kv[0]] = parseInt(kv[1]);
            });

            angular.forEach($scope.filters.defaults, function (value, filter) {
                if (filters_dict[filter] === undefined) {
                    filters_dict[filter] = value;
                }
            });

            return filters_dict;
        },

        update: function (filter, choice) {
            $scope.dropdownIsOpen = false;
            $scope.filters.selected[filter] = choice;

            $scope.filters.updateSearchFilters();

            updateActionLog();
        }
    };

    var updateActionLog = function () {
        var query_filters = $scope.filters.getSearchFilters();

        api.actionLog.list(query_filters).then(function (data) {
            $scope.actionLogItems = data.actionLogItems;
            $scope.filters.items = data.filters;

            angular.forEach(data.filters, function (items, filter) {
                var set_filter = query_filters[filter] !== undefined ? query_filters[filter] :
                    ($scope.filters.defaults[filter] !== undefined ? $scope.filters.defaults[filter] : 0);

                $scope.filters.selected[filter] = $scope.filters.getFilterByKey(filter, set_filter);
            });
        });
    };

    updateActionLog();

}]);
