/*global $,oneApp,moment,constants,angular*/
'use strict';

oneApp.directive('zemChart', ['config', '$compile', '$window', function (config, $compile, $window) {
    return {
        restrict: 'E',
        scope: {
            data: '=zemData',
            metricOptions: '=zemMetricOptions',
            metric1: '=zemMetric1',
            metric2: '=zemMetric2',
            minDate: '=zemMinDate',
            maxDate: '=zemMaxDate',
            onRemove: '&zemOnRemove',
            localStoragePrefix: '=localStoragePrefix'
        },
        templateUrl: '/partials/zem_chart.html',
        controller: ['$scope', '$element', '$attrs', '$http', 'zemUserSettings', function ($scope, $element, $attrs, $http, zemUserSettings) {
            var totalsColor = ['#009db2', '#c9eaef'];
            var colors = [
                ['#d35400', '#eebe9e'],
                ['#1abc9c', '#d6f3ed'],
                ['#34495e', '#d6dbdf'],
                ['#f39c12', '#fdebd0']
            ];
            var commonYAxisMetricIds = ['clicks', 'visits', 'pageviews'];

            var usedColors = {};

            function getMetric2Options (metricOptions) {
                // add (default) option to disable second metric
                return $.merge([{'value': 'none', 'name': 'None'}], metricOptions);
            }

            $scope.hasData = true;
            $scope.legendItems = [];
            $scope.appConfig = config;

            $scope.metric2Options = getMetric2Options($scope.metricOptions);
            $scope.metrics = {
                metric1: $scope.metric1,
                metric2: $scope.metric2
            };

            $scope.$watch('metrics.metric1', function (newValue) {
                // we use $scope.metrics because ui-select doesn't work well with
                // simple variables on scope as ng-model, it is recommended to use a
                // property on an object on scope
                // (https://github.com/angular-ui/ui-select/wiki/FAQs#ng-model-not-working-with-a-simple-variable-on-scope)
                $scope.metric1 = newValue;
            }, true);

            $scope.$watch('metrics.metric2', function (newValue) {
                // we use $scope.metrics because ui-select doesn't work well with
                // simple variables on scope as ng-model, it is recommended to use a
                // property on an object on scope
                // (https://github.com/angular-ui/ui-select/wiki/FAQs#ng-model-not-working-with-a-simple-variable-on-scope)
                $scope.metric2 = newValue;
            }, true);

            $scope.$watch('metric1', function (newValue) {
                $scope.metrics.metric1 = newValue;
            }, true);

            $scope.$watch('metric2', function (newValue) {
                $scope.metrics.metric2 = newValue;
            }, true);

            $scope.$watch('metricOptions', function (newValue) {
                $scope.metric2Options = getMetric2Options($scope.metricOptions);
            }, true);

            $scope.getSelectedName = function (selected) {
                // Returns the name of the selected item. ui-select doesn't update the name correctly when choices change
                // so the right name is returned here.
                if (!selected) {
                    return '';
                }

                for (var i = 0; i < $scope.metric2Options.length; i++) {
                    if ($scope.metric2Options[i].value === selected.value) {
                        return $scope.metric2Options[i].name;
                    }
                }
                return '';
            };

            $scope.chartMetric1Update = function () {
                zemUserSettings.setValue('chartMetric1', $scope.metrics.metric1, $scope.localStoragePrefix);
            };

            $scope.chartMetric2Update = function () {
                zemUserSettings.setValue('chartMetric2', $scope.metrics.metric2, $scope.localStoragePrefix);
            };

            $scope.config = {
                options: {
                    chart: {
                    },
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

            angular.element($window).bind('resize', function () {
                var chart = $('.chart').highcharts();

                var w = $('.chart').parent().width(),
                    h = $('.chart').height();
                // setsize will trigger the graph redraw
                chart.setSize(w, h, false);
            });

            $scope.$watch('data', function (newValue, oldValue) {
                var i = 0,
                    data = newValue && newValue.groups,
                    seriesData = null,
                    metrics = null,
                    metricIds = null,
                    seriesName = null;

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
                    $scope.config.options.xAxis.min = moment($scope.minDate).subtract($scope.minDate.zone(), 'minutes').valueOf();
                    $scope.config.options.xAxis.max = moment($scope.maxDate).subtract($scope.maxDate.zone(), 'minutes').valueOf();
                } else {
                    $scope.config.options.xAxis.min = null;
                    $scope.config.options.xAxis.max = null;
                }

                // currently selected metric ids
                metricIds = [$scope.metric1];
                if ($scope.metric2) {
                    metricIds.push($scope.metric2);
                }

                setAxisFormats(metricIds);
                clearUsedColors(data);

                data.forEach(function (group) {
                    if (group.id !== 'totals') {
                        return;
                    }
                    updateSeries(group, metricIds);
                });

                updateCampaignGoals(newValue.campaignGoals, newValue.goalFields);

                data.forEach(function (group) {
                    if (group.id === 'totals') {
                        return;
                    }
                    updateSeries(group, metricIds);
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

            var updateSeries = function (group, metricIds) {
                var color = getColor(group),
                    commonYAxis = null;
                addLegendItem(color, group, true);

                commonYAxis = true;
                metricIds.forEach(function (metricId, index) {
                    if (commonYAxisMetricIds.indexOf(metricId) === -1) {
                        commonYAxis = false;
                    }
                });

                metricIds.forEach(function (metricId, index) {
                    var seriesData = group.seriesData[metricId] || [],
                        seriesName = group.name + ' (' + getMetricName(metricId)  + ')';
                    if (seriesData.length) {
                        $scope.hasData = true;
                    }

                    seriesData = transformDate(seriesData);
                    seriesData = fillGaps(seriesData);

                    $scope.config.series.unshift({
                        name: seriesName,
                        color: color[index],
                        yAxis: commonYAxis ? 0 : index,
                        data: seriesData,
                        tooltip: {
                            pointFormat: '<div class="color-box" style="background-color: ' + color[index] + '"></div>' + seriesName + ': <b>' + getPointFormat(metricId) + '</b></br>'
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
            };

            var updateCampaignGoals = function (campaignGoals, fieldGoalMap) {
                if (!campaignGoals || !fieldGoalMap) {
                    return;
                }
                var goal1 = fieldGoalMap[$scope.metric1],
                    goal2 = fieldGoalMap[$scope.metric2],
                    commonYAxis = true,
                    metricIds = [],
                    index = 0;

                if (goal1 && $scope.metric1 && campaignGoals[goal1.id]) {
                    metricIds.push($scope.metric1);
                } else {
                    index += 1;
                }
                if (goal2 && $scope.metric2 && campaignGoals[goal2.id]) {
                    if ($scope.metric2 !== $scope.metric1) {
                        metricIds.push($scope.metric2);
                    }
                }

                metricIds.forEach(function (metricId) {
                    var goal = fieldGoalMap[metricId],
                        color = getColor(goal);
                    addLegendItem(color, goal, false, metricIds.indexOf(metricId) + 1);
                    campaignGoals[goal.id].forEach(function (rawSeries) {
                        var series = transformDate(rawSeries);
                        if (commonYAxisMetricIds.indexOf(metricId) === -1) {
                            commonYAxis = false;
                        }
                        addGoalSeries(metricId, goal.name, series, color[index], commonYAxis ? 0 : index);
                    });

                    index += 1;
                });
            };

            var addGoalSeries = function (metricId, goalName, series, color, yAxisIndex) {
                if (!goalName) {
                    return;
                }

                $scope.config.series.push({
                    name: goalName,
                    color: color,
                    yAxis: yAxisIndex,
                    data: series,
                    step: true,
                    dashStyle: 'ShortDash',
                    connectNulls: true,
                    tooltip: {
                        pointFormat: '<div class="color-box" style="background-color: ' + color + '"></div>' + goalName + ': <b>' + getPointFormat(metricId) + '</b></br>'
                    },
                    marker: {
                        enabled: false,
                    },
                });
            };

            /////////////
            // helpers //
            /////////////

            var metricFormats = {};
            metricFormats[constants.chartMetric.CPC] = {'type': 'currency', 'fractionSize': 3};
            metricFormats[constants.chartMetric.COST] = {'type': 'currency', 'fractionSize': 2};
            metricFormats[constants.chartMetric.DATA_COST] = {'type': 'currency', 'fractionSize': 2};
            metricFormats[constants.chartMetric.EFFECTIVE_DATA_COST] = {'type': 'currency', 'fractionSize': 2};
            metricFormats[constants.chartMetric.MEDIA_COST] = {'type': 'currency', 'fractionSize': 2};
            metricFormats[constants.chartMetric.EFFECTIVE_MEDIA_COST] = {'type': 'currency', 'fractionSize': 2};
            metricFormats[constants.chartMetric.TOTAL_COST] = {'type': 'currency', 'fractionSize': 2};
            metricFormats[constants.chartMetric.BILLING_COST] = {'type': 'currency', 'fractionSize': 2};
            metricFormats[constants.chartMetric.LICENSE_FEE] = {'type': 'currency', 'fractionSize': 2};
            metricFormats[constants.chartMetric.CTR] = {'type': 'percent', 'fractionSize': 2};
            metricFormats[constants.chartMetric.NEW_USERS] = {'type': 'percent', 'fractionSize': 2};
            metricFormats[constants.chartMetric.BOUNCE_RATE] = {'type': 'percent', 'fractionSize': 2};
            metricFormats[constants.chartMetric.PV_PER_VISIT] = {'fractionSize': 2};
            metricFormats[constants.chartMetric.AVG_TOS] = {'type': 'time', 'fractionSize': 1};
            metricFormats[constants.chartMetric.CLICK_DISCREPANCY] = {'type': 'percent', 'fractionSize': 2};
            metricFormats[constants.chartMetric.TOTAL_SECONDS] = {};
            metricFormats[constants.chartMetric.TOTAL_PAGEVIEWS] = {};
            metricFormats[constants.chartMetric.UNBOUNCED_VISITS] = {};
            metricFormats[constants.chartMetric.COST_PER_SECOND] = {'type': 'currency', 'fractionSize': 2};
            metricFormats[constants.chartMetric.COST_PER_PAGEVIEW] = {'type': 'currency', 'fractionSize': 2};
            metricFormats[constants.chartMetric.COST_PER_UNBOUNCED_VISITOR] = {'type': 'currency', 'fractionSize': 2};
            metricFormats[constants.chartMetric.COST_PER_NEW_VISITOR] = {'type': 'currency', 'fractionSize': 2};
            metricFormats[constants.chartMetric.COST_PER_CONVERSION_GOAL_1] = {'type': 'currency', 'fractionSize': 2};
            metricFormats[constants.chartMetric.COST_PER_CONVERSION_GOAL_2] = {'type': 'currency', 'fractionSize': 2};
            metricFormats[constants.chartMetric.COST_PER_CONVERSION_GOAL_3] = {'type': 'currency', 'fractionSize': 2};
            metricFormats[constants.chartMetric.COST_PER_CONVERSION_GOAL_4] = {'type': 'currency', 'fractionSize': 2};
            metricFormats[constants.chartMetric.COST_PER_CONVERSION_GOAL_5] = {'type': 'currency', 'fractionSize': 2};

            var getMetricName = function (metricId) {
                var name = null;
                $scope.metricOptions.forEach(function (option) {
                    if (option.value === metricId) {
                        name = option.name;
                    }
                });

                return name;
            };

            var getPointFormat = function (metricId) {
                var format = null;
                var valueSuffix = '';
                var valuePrefix = '';
                var fractionSize = 0;

                format = metricFormats[metricId];

                if (format !== undefined) {
                    fractionSize = format.fractionSize;

                    if (format.type === 'currency') {
                        valuePrefix = '$';
                    } else if (format.type === 'percent') {
                        valueSuffix = '%';
                    } else if (format.type === 'time') {
                        valueSuffix = 's';
                    }
                }

                return valuePrefix + '{point.y:,.' + fractionSize + 'f}' + valueSuffix;
            };

            var setAxisFormats = function (metricIds) {
                var format = null;
                var axisFormat = null;

                metricIds.forEach(function (metricId, index) {
                    format = metricFormats[metricId];
                    axisFormat = null;
                    if (format !== undefined) {
                        if (format.type === 'currency') {
                            axisFormat = '${value}';
                        } else if (format.type === 'percent') {
                            axisFormat = '{value}%';
                        } else if (format.type === 'time') {
                            axisFormat = '{value}s';
                        }
                    }

                    $scope.config.options.yAxis[index].labels = {
                        format: axisFormat
                    };
                });
            };

            var transformDate = function (data) {
                return data.map(function (item) {
                    item[0] = parseInt(moment.utc(item[0]).format('XSSS'), 10);
                    return item;
                });
            };

            var fillGaps = function (stats) {
                if (stats.length < 2) {
                    return stats;
                }

                var ts, usedDates = {},
                    startTS = stats[0][0],
                    endTS = stats[stats.length - 1][0];

                // mark which for which dates do we have data points
                for (var i = 0; i < stats.length; i++) {
                    usedDates[stats[i][0]] = stats[i];
                }

                var previousMissing = false, statsNoGaps = [], msInADay = 24 * 3600 * 1000;

                // fill in the necessary null datapoints, so that the chart does not
                // contain lines through dates that do not have data
                for (var d = startTS; d < endTS + msInADay; d += msInADay) {
                    if (d in usedDates) {
                        statsNoGaps.push(usedDates[d]);
                        previousMissing = false;
                    } else if (!previousMissing) {
                        // no need to fill all the missing dates
                        // fill only one after a non-null datapoint
                        statsNoGaps.push([d, null]);
                        previousMissing = true;
                    }
                }
                return statsNoGaps;
            };

            var clearUsedColors = function (data) {
                // clean usedColors of all groupIds that are not selected anymore
                var groupId = null;
                var groupIds = data.map(function (group) {
                    return group.id.toString();
                });

                for (groupId in usedColors) {
                    if (!usedColors.hasOwnProperty(groupId)) {
                        continue;
                    }

                    if (groupIds.indexOf(groupId.toString()) === -1) {
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

            var addLegendItem = function (color, group, removable, index) {
                if (index === undefined) {
                    index = $scope.legendItems.length;
                }
                var legendItem = {
                    id: group.id,
                    name: group.name,
                    color1: color[0],
                    color2: color[1],
                    removable: removable,
                };

                if (legendItem.id === 'totals') {
                    $scope.legendItems.unshift(legendItem);
                } else {
                    var exists = false;
                    $scope.legendItems.forEach(function (legendItem) {
                        if (legendItem.name === group.name) {
                            exists = true;
                        }
                    });
                    if (!exists) {
                        $scope.legendItems.splice(index, 0, legendItem);
                    }
                }
            };
        }]
    };
}]);
