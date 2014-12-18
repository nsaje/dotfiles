/*global $,oneApp,constants*/
"use strict";

oneApp.directive('zemTable', ['config', function(config) {
    return {
        restrict: 'E',
        scope: {
            showLoader: '=zemTableShowLoader',
            columns: '=zemTableColumns',
            rows: '=zemTableRows',
            totalRow: '=zemTableTotalRow',
            notifications: '=zemTableNotifications',
            order: '=zemTableOrder',
            orderCallback: '&zemTableOrderCallback'
        },
        templateUrl: '/partials/zem_table.html',
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {
            $scope.config = config;
            $scope.numberColumnTypes = ['currency', 'percent', 'number', 'seconds', 'datetime'];
            $scope.selectedRowsCount = 0;
            $scope.constants = constants;
            
            $scope.isNumberColumnType = function (columnType) {
                return $scope.numberColumnTypes.indexOf(columnType) > -1;
            };

            $scope.callOrderCallback = function (field) {
                var i;
                var initialOrder;
                var orderField;

                if ($scope.order === field) {
                    $scope.order = '-' + field;
                } else if ($scope.order === '-' + field) {
                    $scope.order = field;
                } else {
                    for (i = 0; i < $scope.columns.length; i++) {
                        orderField = $scope.columns[i].orderField || $scope.columns[i].field;
                        if (orderField === field) {
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
                callback(row, checked);
            };

            $scope.isFieldEditable = function (editableFields, field) {
                if (!editableFields) {
                    return false;
                }

                return editableFields.indexOf(field) !== -1;
            };

            $scope.getSettingsFieldMessage = function (row) {
                return row.maintenance ? 
                    'This value cannot be edited because the media source is currently in maintenance.' : 
                    'This media source doesn\'t support setting this value through the dashboard.';
            };
        }]
    };
}]);
