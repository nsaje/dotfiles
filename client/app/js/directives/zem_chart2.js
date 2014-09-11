/*global $,oneApp,moment*/
"use strict";

oneApp.directive('zemChart2', ['config', function(config) {
    return {
        restrict: 'E',
        scope: {
            data: '=zemData',
            metric1: '=zemMetric1',
            metricValues: '=zemMetricValues',
            metric2: '=zemMetric2',
            minDate: '=zemMinDate',
            maxDate: '=zemMaxDate',
            onRemove: '&zemOnRemove'
        },
        templateUrl: config.static_url + '/partials/zem_chart2.html',
        controller: ['$scope', '$element', '$attrs', '$http', function ($scope, $element, $attrs, $http) {

            var totalsColor = ['#009db2', '#c9eaef'];
            var colors = [
                ['#d35400', '#eebe9e'],
                ['#1abc9c', '#d6f3ed'],
                ['#34495e', '#d6dbdf'],
                ['#f39c12', '#fdebd0']
            ];
            var usedColors = {};

            $scope.hasData = true;
            $scope.legendItems = [];
            $scope.appConfig = config;

            $scope.config = {
                options: {
                    title: {
                        text: null
                    },
                    xAxis: {
                        type: 'datetime',
                        minTickInterval: 24 * 3600 * 1000
                    },
                    yAxis: [{
                        title: {
                            text: null
                        },
                        min: 0,
                        lineColor: null,
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
                        lineColor: null,
                        lineWidth: 2,
                        plotLines: [{
                            value: 0,
                            width: 1
                        }],
                        opposite: true
                    }],
                    tooltip: {
                        shared: true,
                        useHTML: true,
                        headerFormat: '<div class="tooltip-header">{point.key}</div>',
                        backgroundColor: '#fff',
                        borderColor: '#d2d2d2',
                        shadow: false,
                    },
                    plotOptions: {
                        series: {
                            marker: {
                                states: {
                                    hover: {
                                        radius: 3
                                    }
                                }
                            }
                        }
                    },
                    legend: {
                        enabled: false
                    },
                    credits: {
                        enabled: false
                    }
                }
            };

            $scope.$watch('data', function(newValue, oldValue) {
                var i = 0;
                var data = newValue;
                var color = null;
                var metric = null;

                $scope.hasData = false;
                $scope.legendItems = [];
                $scope.config.series = [];

                // Undefined means that no data has been assigned yet but will be.
                if (data === undefined) {
                    $scope.hasData = true;
                    return;
                }

                // Set min and max only if start date and end date are different. If
                // they are the same, let charts figure it out because otherwise it
                // renders strangely.
                if ($scope.minDate.valueOf() !== $scope.maxDate.valueOf()) {
                    $scope.config.options.xAxis.min = moment($scope.minDate).add('minutes', $scope.minDate.zone()).valueOf();
                    $scope.config.options.xAxis.max = moment($scope.maxDate).subtract('minutes', $scope.maxDate.zone()).valueOf();
                } else {
                    $scope.config.options.xAxis.min = null;
                    $scope.config.options.xAxis.max = null;
                }

                setAxisFormats(data);
                clearUsedColors(data);

                data.seriesGroups.forEach(function (group) {
                    color = getColor(group);
                    addLegendItem(color, group);

                    group.seriesData.forEach(function (seriesData, index) {
                        metric = data.metrics[index];
                        if (!metric) {
                            return;
                        }

                        if (seriesData.length) {
                            $scope.hasData = true;
                        }

                        $scope.config.series.push({
                            name: group.name + ' (' + metric.name  + ')',
                            color: color[index],
                            yAxis: index,
                            data: seriesData,
                            tooltip: {
                                valueSuffix: metric.valueSuffix,
                                valuePrefix: metric.valuePrefix
                            },
                            marker: {
                                radius: 3,
                                symbol: 'square',
                                fillColor: color[index],
                                lineWidth: 2,
                                lineColor: null
                            }
                        });
                    });
                });
            
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


            // helpers

            var setAxisFormats = function (data) {
                var axisFormat = null;

                data.metrics.forEach(function (metric, index) {
                    axisFormat = null;

                    if (!metric) {
                        return;
                    }

                    if (metric.format === 'currency') {
                        metric.valuePrefix = '$';
                        axisFormat = '${value}';
                    } else if (metric.format === 'percent') {
                        metric.valueSuffix = '%';
                        axisFormat = '{value}%';
                    }
                    
                    $scope.config.options.yAxis[index].labels = {
                        format: axisFormat
                    };
                });
            };

            var clearUsedColors = function (data) {
                // clean usedColors of all groupIds that are not selected anymore
                var groupId = null;
                var groupIds = data.seriesGroups.map(function (group) {
                    return group.id;
                });

                for (groupId in usedColors) {
                    if (!usedColors.hasOwnProperty(groupId)) {
                        continue;
                    }

                    if (groupIds.indexOf(groupId) === -1) {
                        delete usedColors[groupId];
                    }
                }
            };

            var getColor = function (group) {
                var color = null;
                var usedColorIndexes = null;
                var i = 0;

                if (group.id === 'totals') {
                    return totalsColor;
                }

                // check if group had been assigned a color before
                color = colors[usedColors[group.id]];

                // if not, select one of the available colors
                if (!color) {
                    usedColorIndexes = Object.keys(usedColors).map(function (key) {
                        return usedColors[key];
                    });

                    for (i = 0; i < colors.length; i++) {
                        if (usedColorIndexes.indexOf(i) !== -1) {
                            continue;
                        }

                        color = colors[i];
                        usedColors[group.id] = i;
                        break;
                    }
                }

                return color;
            };

            var addLegendItem = function (color, group) {
                var legendItem = {
                    id: group.id,
                    name: group.name,
                    color1: color[0],
                    color2: color[1]
                };

                if (legendItem.id === 'totals') {
                    $scope.legendItems.unshift(legendItem);
                } else {
                    $scope.legendItems.push(legendItem);
                }
            }
        }]
    };
}]);
