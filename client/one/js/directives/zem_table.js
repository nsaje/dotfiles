/*global $,oneApp,constants*/
"use strict";

oneApp.directive('zemTable', ['config', '$window', function(config, $window) {
    return {
        restrict: 'E',
        scope: {
            showLoader: '=zemTableShowLoader',
            columns: '=zemTableColumns',
            rows: '=zemTableRows',
            totalRow: '=zemTableTotalRow',
            notifications: '=zemTableNotifications',
            order: '=zemTableOrder',
            orderCallback: '&zemTableOrderCallback',
            dataStatus: '=zemTableDataStatus'
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

            $scope.isFieldEditable = function (row, field) {
                var editableFields = row.editable_fields;
                if (!editableFields) {
                    return false;
                }

                if (field in editableFields) {
                    return editableFields[field].enabled;
                }

                return false;
            };

            $scope.getSettingsFieldMessage = function (row, field) {
                var editableFields = row.editable_fields;
                if (!editableFields) {
                    return '';
                }

                return editableFields[field].message;
            };

            $scope.openUrl = function(data, $event) {
                $event.stopPropagation();
                $event.preventDefault();
                $window.open(data.destinationUrl || data.url, '_blank');
            };

            // HACK: campaign goals experiment
            // to be removed by 20. 11. 2015
            $scope.getRowStyle = function(row) {
                // check user
                var allowedUsers = [5, 8, 13, 70];
                if (allowedUsers.indexOf(parseInt($scope.$parent.user.id)) === -1) {
                    return;
                }

                // check account
                if ($scope.$parent.account.id !== 11) {
                    return;
                }

                var color = 'inherit';
                if ((row.cpc && row.cpc >= 0.12) || (row.bounce_rate && row.bounce_rate >= 85)) {
                    color = '#ffb4b4';
                } else if ((row.cpc && row.cpc <= 0.09) || (row.bounce_rate && row.bounce_rate <= 40)) {
                    color = '#b4ffb4';
                }
                return {'background-color': color};
            };
        }]
    };
}]);
