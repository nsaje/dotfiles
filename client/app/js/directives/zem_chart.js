/*global $,oneApp*/
"use strict";

oneApp.directive('zemChart', ['config', function(config) {
    return {
        restrict: 'E',
        scope: {
            data: '=zemData',
            metric1: '=zemMetric1',
            metric1Values: '=zemMetric1Values',
            metric2: '=zemMetric2',
            metric2Values: '=zemMetric2Values'
        },
        templateUrl: config.static_url + '/partials/zem_chart.html',
        controller: ['$scope', '$element', '$attrs', '$http', function ($scope, $element, $attrs, $http) {

            var markerSymbols = ["circle", "square", "diamond", "triangle", "triangle-down"];
            var colors = ['#2fa8c7', '#4bbc00'];
            $scope.hasData = true;

            $scope.config = {
                options: {
                    title: {
                        text: null
                    },
                    colors: colors,
                    xAxis: {
                        type: 'datetime'
                        /* categories: [] */
                    },
                    yAxis: [{
                        title: {
                            text: null
                        },
                        min: 0,
                        lineColor: colors[0],
                        lineWidth: 2,
                        plotLines: [{
                            value: 0,
                            width: 1
                        }]
                    }, {
                        title: {
                            text: null
                        },
                        min: 0,
                        lineColor: colors[1],
                        lineWidth: 2,
                        plotLines: [{
                            value: 0,
                            width: 1
                        }],
                        opposite: true
                    }],
                    legend: {
                        enabled: false
                    },
                    credits: {
                        enabled: false
                    }
                },
                series: [{
                    name: null,
                    color: colors[0],
                    yAxis: 0,
                    data: [],
                    tooltip: {
                        valueSuffix: null
                    }
                }, {
                    name: null,
                    color: colors[1],
                    yAxis: 1,
                    data: [],
                    tooltip: {
                        valueSuffix: null
                    }
                }]
            };

            $scope.$watch('data', function(newValue, oldValue) {
                var i = 0;
                var j = 0;
                var k = 0;
                var metrics = [];
                var data = [];
                var valuePrefix = null;
                var valueSuffix = null;
                var axisFormat = null;
                var name = null;
                var markerRadius = 2;

                $scope.hasData = false;

                // Undefined means that no data has been assigned yet but will be.
                if (newValue === undefined) {
                    $scope.hasData = true;
                    return;
                }
            
                if (newValue && Object.keys(newValue).length) {
                    // if (newValue.xType !== 'categories') {
                    //     $scope.config.options.xAxis.type = newValue.xType;
                    // } else {
                    //     $scope.config.options.xAxis.categories = newValue.x;
                    // }
                    $scope.config.series = [];

                    for (i = 0; i < $scope.metric1Values.length; i++) {
                        if ($scope.metric1Values[i].value === $scope.metric1) {
                            metrics.push($scope.metric1Values[i].name);
                            break;
                        }
                    }

                    if ($scope.metric2Values && $scope.metric2Values.length) {
                        for (i = 0; i < $scope.metric2Values.length; i++) {
                            if ($scope.metric2Values[i].value === $scope.metric2) {
                                metrics.push($scope.metric2Values[i].name);
                                break;
                            }
                        }
                    }

                    data = newValue.data;
                    for (i = 0; i < data.length; i++) {
                        for (j = 0; j < data[i].length; j++) {
                            valuePrefix = null;
                            valueSuffix = null;
                            axisFormat = null;

                            if (newValue.formats[j] === 'currency') {
                                valuePrefix = '$';
                                axisFormat = '${value}';
                            } else if (newValue.formats[j] === 'percent') {
                                valueSuffix = '%';
                                axisFormat = '{value}%';
                            }
                            
                            $scope.config.options.yAxis[j].labels = {
                                format: axisFormat
                            };

                            name = metrics[j];
                            if (newValue.names.length) {
                                name = newValue.names[i] + ', ' + name;
                            }

                            $scope.config.series.push({
                                name: name,
                                color: colors[j],
                                yAxis: j,
                                data: data[i][j],
                                tooltip: {
                                    valueSuffix: valueSuffix,
                                    valuePrefix: valuePrefix
                                },
                                marker: {
                                    radius: markerRadius,
                                    symbol: markerSymbols[i % markerSymbols.length],
                                    fillColor: '#fff',
                                    lineWidth: 2,
                                    lineColor: null
                                }
                            });
                            for (k = 0; k < data[i][j].length; k++) {
                                if ((!Array.isArray(data[i][j][k]) && data[i][j][k]) || data[i][j][k][data[i][j][k].length-1]) {
                                    $scope.hasData = true;
                                    break;
                                }
                            }
                        }

                        // When we run out of marker symbols, start increasing their
                        // sizes so that user can distinguish between them.
                        if (i > 0 && i % markerSymbols.length === 0) {
                            markerRadius += 2;
                        }
                    }
                }

                // HACK: we need this in order to force the chart to display
                // x axis with value 0 on the bottom of the graph if there is
                // no data to be displayed (or is always 0).
                if (!$scope.hasData) {
                    for (i = 0; i < $scope.config.options.yAxis.length; i++) {
                        $scope.config.options.yAxis[i].max = 10;
                    }
                } else {
                    for (i = 0; i < $scope.config.options.yAxis.length; i++) {
                        $scope.config.options.yAxis[i].max = null;
                    }
                }
            });
        }]
    };
}]);
