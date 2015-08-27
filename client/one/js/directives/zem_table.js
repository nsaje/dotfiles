/*global $,oneApp,constants*/
"use strict";

oneApp.directive('zemTable', ['config', '$window',  function(config, $window) {
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
        controller: ['$scope', '$state', '$location', '$element', '$attrs', 'zemUserSettings', function ($scope, $state, $location, $element, $attrs, zemUserSettings) {
            $scope.config = config;
            $scope.numberColumnTypes = ['currency', 'percent', 'number', 'seconds', 'datetime'];
            $scope.selectedRowsCount = 0;
            $scope.constants = constants;
            
        
            $scope.isNumberColumnType = function (columnType) {
                return $scope.numberColumnTypes.indexOf(columnType) > -1;
            };

            function filterAndFormatParams(dict) {
                var str = [];
                var transferredParams = ['start_date', 'end_date', 'filtered_sources', 'show_archived'];
                for(var p in dict) {
                    if (transferredParams.indexOf(p) > -1) {
                        str.push(encodeURIComponent(p) + "=" + encodeURIComponent(dict[p]));
                    }
                }
                return str.join("&");
            };            
            $scope.linkNavClick = function(field_data, event) {
                event.stopPropagation();
                if (event.which === 1 && !event.metaKey && !event.ctrlKey) {
                    $state.go(field_data.state, {id: field_data.id});
                } else if (event.which === 2 || (event.which ===1 && (event.metaKey || event.ctrlKey))) {
                    // MIDDLE CLICK or CMD+LEFTCLICK - new tab
                    var url_bare = $state.href(field_data.state, {id: field_data.id});
                    var url_full = url_bare + "?" + filterAndFormatParams($location.search());
                    $window.open(url_full, "_blank");
                 }
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
        }]
    };
}]);
