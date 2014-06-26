/*global $,oneApp*/
"use strict";

oneApp.directive("zemChart", function() {
    return {
        restrict: 'E',
        scope: {
            data: '=zemData',
            metric1: '=zemMetric1',
            metric1Values: '=zemMetric1Values',
            metric2: '=zemMetric2',
            metric2Values: '=zemMetric2Values'
        },
        templateUrl: 'http://localhost:9999/partials/zem_chart.html',
        controller: ['$scope', '$element', '$attrs', '$http', function ($scope, $element, $attrs, $http) {

            var colors = ['#2fa8c7', '#4bbc00'];
            var hasData = false;

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
                var i = 0,
                    j = 0,
                    metrics = [];

                hasData = false;
            
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

                    for (i = 0; i < newValue.length; i++) {
                        $scope.config.series.push({
                            name: metrics[i],
                            color: colors[i],
                            yAxis: i,
                            data: newValue[i],
                            tooltip: {
                                valueSuffix: null
                            },
                            marker: {
                                radius: 2,
                                symbol: 'circle',
                                fillColor: '#fff',
                                lineWidth: 2,
                                lineColor: null
                            }
                        });
                        for (j = 0; j < newValue[i].length; j++) {
                            if ((!Array.isArray(newValue[i][j]) && newValue[i][j]) || newValue[i][j][newValue[i][j].length-1]) {
                                hasData = true;
                                break;
                            }
                        }
                    }
                }

                // HACK: we need this in order to force the chart to display
                // x axis with value 0 on the bottom of the graph if there is
                // no data to be displayed (or is always 0).
                if (!hasData) {
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
});
