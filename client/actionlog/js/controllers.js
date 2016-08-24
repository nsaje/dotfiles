actionLogApp.controller('ActionLogCtrl', ['$scope', '$location', '$modal', 'config', 'api', function ($scope, $location, $modal, config, api) {

    $scope.user = null;
    $scope.actionLogItems = null;
    $scope.actionLogItemsMax = null;
    $scope.pixelData = {};
    $scope.errors = {};

    $scope.states = [
        [actionLogConstants.state.FAILED.name, actionLogConstants.state.FAILED.value],
        [actionLogConstants.state.WAITING.name, actionLogConstants.state.WAITING.value],
        [actionLogConstants.state.SUCCESS.name, actionLogConstants.state.SUCCESS.value],
    ];
    $scope.stateClass = function (log, state) {
        var cls = 'btn-' + state[0].toLowerCase();

        if (log.state[1] === state[1]) {
            cls += ' state-selected';
        }
        return cls;
    };
    $scope.updateState = function (log, state) {
        // if creating pixel and action is successful
        if (log.action == 'create_pixel' && state[1] == actionLogConstants.state.SUCCESS.value) {
            $modal.open({
                templateUrl: config.static_url + '/actionlog/pixel_modal.html',
                scope: $scope,
                controller: ['$scope', '$modalInstance', function ($scope, $modalInstance) {
                    $scope.ok = function () {
                        executeUpdatePixel(log, state, $modalInstance);
                    };

                    $scope.cancel = function () {
                        $modalInstance.dismiss('cancel');
                    };
                }],
                size: 'lg',
            });
        } else {
            executeSave(log, state);
        }
    };

    function executeUpdatePixel(log, state, $modalInstance) {
        api.actionLog.updateOutbrainSourcePixel(log.conversion_pixel[1], $scope.pixelData.url, $scope.pixelData.id)
            .then(function (data) {
                executeSave(log, state);
                $modalInstance.close();
                $scope.pixelData = {};
            },
            function (data) {
                $scope.errors = data;
            });
    }

    function executeSave(log, state) {
        api.actionLog.save_state(log.id, state[1]).then(function (data) {
            log.state = data.actionLogItem.state;
            log.modified_dt = data.actionLogItem.modified_dt;
            log.modified_by = data.actionLogItem.modified_by;
        });
    }

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
            var str_filters = [];
            for (var prop in $scope.filters.selected) {
                if ($scope.filters.selected.hasOwnProperty(prop)) {
                    str_filters.push([prop, $scope.filters.selected[prop][0]].join(':'));
                }
            }

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
            $scope.filters.selected[filter] = choice;

            $scope.filters.updateSearchFilters();

            updateActionLog();
        }
    };

    $scope.$watch('actionLogItems', function (newVal, oldVal) {
        if (!newVal) {
            return;
        }

        var orderPrevious = null, orderClassVal = 0;
        var getOrderClass = function (log) {
            if (log.order !== orderPrevious) {
                orderPrevious = log.order;
                orderClassVal ^= 1;
            }
            return 'order-class-' + orderClassVal;
        };

        newVal.map(function (log) {
            log.orderClass = getOrderClass(log);
        });
    });

    var updateActionLog = function () {
        var query_filters = $scope.filters.getSearchFilters();

        api.actionLog.list(query_filters).then(function (data) {
            $scope.actionLogItems = data.actionLogItems;
            $scope.actionLogItemsMax = data.actionLogItemsMax;
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
