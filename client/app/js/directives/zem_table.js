/*global $,oneApp*/
"use strict";

oneApp.directive('zemTable', ['config', function(config) {
    return {
        restrict: 'E',
        scope: {
            showLoader: '=zemTableShowLoader',
            columns: '=zemTableColumns',
            rows: '=zemTableRows',
            totalRow: '=zemTableTotalRow',
            order: '=zemTableOrder',
            orderCallback: '&zemTableOrderCallback'
        },
        templateUrl: config.static_url + '/partials/zem_table.html',
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {
            $scope.numberColumnTypes = ['currency', 'percent', 'number', 'datetime'];
            $scope.selectedRowsCount = 0;
            
            $scope.isNumberColumnType = function (columnType) {
                return $scope.numberColumnTypes.indexOf(columnType) > -1;
            };

            $scope.callOrderCallback = function (field) {
                var i;
                var initialOrder;

                if ($scope.order === field) {
                    $scope.order = '-' + field;
                } else if ($scope.order === '-' + field) {
                    $scope.order = field;
                } else {
                    for (i = 0; i < $scope.columns.length; i++) {
                        if ($scope.columns[i].field === field) {
                            initialOrder = $scope.columns[i].initialOrder;
                            break;
                        }
                    }

                    if (initialOrder === 'asc') {
                        $scope.order = field;
                    } else if (initialOrder === 'desc') {
                        $scope.order = '-' + field;
                    }
                }

                $scope.orderCallback({order: $scope.order});
            };

            $scope.callSelectCallback = function (callback, row, checked, count) {
                // if (count) {
                //     if (checked) {
                //         $scope.selectedRowsCount++;
                //     } else {
                //         $scope.selectedRowsCount--;
                //     }
                // }

                callback(row, checked);
            };
        }]
    };
}]);
