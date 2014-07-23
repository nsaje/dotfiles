/*global $,oneApp,moment*/
"use strict";

oneApp.directive('zemChart', ['config', function(config) {
    return {
        restrict: 'E',
        scope: {
            data: '=zemData',
            metric1: '=zemMetric1',
            metric1Values: '=zemMetric1Values',
            metric2: '=zemMetric2',
            metric2Values: '=zemMetric2Values',
            minDate: '=zemMinDate',
            maxDate: '=zemMaxDate'
        },
        templateUrl: config.static_url + '/partials/zem_chart.html',
        controller: ['$scope', '$element', '$attrs', '$http', function ($scope, $element, $attrs, $http) {

            var totalsColor = ['#009db2', '#c9eaef'];
            var colors = [
                ['#d35400', '#eebe9e'],
                ['#1abc9c', '#d6f3ed'],
                ['#34495e', '#d6dbdf'],
                ['#f39c12', '#fdebd0']
            ];
            var nameColors = {};

            $scope.hasData = true;

            $scope.config = {
                options: {
                    title: {
                        text: null
                    },
                    xAxis: {
                        type: 'datetime',
                        minTickInterval: 24 * 3600 * 1000
                        /* categories: [] */
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
                var j = 0;
                var k = 0;
                var ci = 0;
                var metrics = [];
                var data = [];
                var valuePrefix = null;
                var valueSuffix = null;
                var axisFormat = null;
                var name = null;
                var color = null;
                var usedColors = [];
                var colorIndex = 0;
                var tempNameColors = {};
                var key = null;

                $scope.hasData = false;

                // Undefined means that no data has been assigned yet but will be.
                if (newValue === undefined) {
                    $scope.hasData = true;
                    return;
                }

                // Set min and max only if start date and end date are different. If
                // they are the sime, let charts figure it out because otherwise it
                // renders strangely.
                if ($scope.minDate.valueOf() !== $scope.maxDate.valueOf()) {
                    $scope.config.options.xAxis.min = moment($scope.minDate).add('minutes', $scope.minDate.zone()).valueOf();
                    $scope.config.options.xAxis.max = moment($scope.maxDate).subtract('minutes', $scope.maxDate.zone()).valueOf();
                } else {
                    $scope.config.options.xAxis.min = null;
                    $scope.config.options.xAxis.max = null;
                }
            
                if (newValue && Object.keys(newValue).length) {
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

                    for (key in nameColors) {
                        if (nameColors.hasOwnProperty(key) && newValue.names.indexOf(key) !== -1) {
                            colorIndex = nameColors[key];

                            usedColors.push(colorIndex);
                            tempNameColors[key] = colorIndex;
                        }
                    }
                    nameColors = tempNameColors;

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

                            if (newValue.names.length) {
                                name = newValue.names[i];
                            }

                            if (name === null || name == undefined) {
                                name = 'Totals';
                                color = totalsColor[j];
                            } else {
                                if (nameColors[name] === undefined) {
                                    for (ci = 0; ci < colors.length; ci++) {
                                        if (usedColors.indexOf(ci) === -1) {
                                            nameColors[name] = ci;
                                            usedColors.push(ci);
                                            break;
                                        }
                                    }   
                                }

                                color = colors[nameColors[name]][j];
                            }

                            $scope.config.series.push({
                                name: name + ' (' + metrics[j] + ')',
                                color: color,
                                yAxis: j,
                                data: data[i][j],
                                tooltip: {
                                    valueSuffix: valueSuffix,
                                    valuePrefix: valuePrefix
                                },
                                marker: {
                                    radius: 3,
                                    symbol: 'square',
                                    fillColor: color,
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
