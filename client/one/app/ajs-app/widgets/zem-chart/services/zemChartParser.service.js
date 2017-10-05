angular.module('one.widgets').service('zemChartParser', function ($window, zemChartMetricsService) {
    var COMMON_Y_AXIS_METRICS = ['clicks', 'visits', 'pageviews'];
    var COLORS = angular.extend({
        TOTALS: ['#3f547f', '#b2bbcc'],
        GOALS: ['#99cc00', '#d6eb99'],
        DATA: [
            ['#29aae3', '#a9ddf4'],
            ['#0aaf9f', '#9ddfd9'],
            ['#f15f74', '#f9bfc7'],
        ]
    }, $window.zOne.whitelabel && (overwrittes[$window.zOne.whitelabel.id] || {}).chartColors || {});

    this.parseMetaData = parseMetaData;
    this.parseData = parseData;

    function parseMetaData (chart, metaData) {
        chart.metrics.options = metaData.metrics;
        chart.metrics.metaData = metaData;
    }

    function parseData (chart, chartData, metrics, dateRange) {
        updateDateRange(chart, dateRange);
        updateAxisFormats(chart, metrics);
        clearUsedColors(chart, chartData.groups);

        applySeries(chart, chartData.groups, metrics);
        applyGoals(chart, chartData, metrics);
        checkEmptyData(chart);
    }

    function applySeries (chart, data, metricIds) {
        data.forEach(function (group) {
            if (group.id === 'totals') {
                return;
            }
            updateSeries(chart, group, metricIds);
        });

        data.forEach(function (group) {
            if (group.id !== 'totals') {
                return;
            }
            updateSeries(chart, group, metricIds);
        });
    }

    function checkEmptyData (chart) {
        var i;
        // HACK: we need this in order to force the chart to display
        // x axis with value 0 on the bottom of the graph if there is
        // no data to be displayed (or is always 0).
        if (!chart.hasData) {
            for (i = 0; i < chart.config.yAxis.length; i++) {
                chart.config.yAxis[i].max = 10;
            }
        } else {
            for (i = 0; i < chart.config.yAxis.length; i++) {
                chart.config.yAxis[i].max = null;
            }
        }
    }

    function updateDateRange (chart, dateRange) {
        // Set min and max only if start date and end date are different. If
        // they are the same, let charts figure it out because otherwise it
        // renders strangely.
        if (dateRange.startDate.valueOf() !== dateRange.endDate.valueOf()) {
            chart.config.xAxis.min = moment(dateRange.startDate)
                .add(dateRange.startDate.utcOffset(), 'minutes')
                .valueOf();
            chart.config.xAxis.max = moment(dateRange.endDate)
                .add(dateRange.endDate.utcOffset(), 'minutes')
                .valueOf();
        } else {
            chart.config.xAxis.min = null;
            chart.config.xAxis.max = null;
        }
    }

    function applyGoals (chart, data, metrics) {
        if (!data.campaignGoals || !data.goalFields) {
            return;
        }

        var goal1 = data.goalFields[metrics[0]];
        var goal2 = data.goalFields[metrics[1]];
        var goals = [];
        var goalIndex;

        if (goal1 && metrics[0] && data.campaignGoals[goal1.id]) {
            goalIndex = 0;
            goals.push(createGoal(chart, data, metrics[0], goalIndex));
        }

        if (goal2 && metrics[1] && data.campaignGoals[goal2.id]) {
            if (metrics[0] !== metrics[1]) {
                goalIndex = 1;
                goals.push(createGoal(chart, data, metrics[1], goalIndex));
            }
        }

        updateCampaignGoals(chart, goals, data.campaignGoals);
    }

    function createGoal (chart, data, metricId, index) {
        var metric = zemChartMetricsService.findMetricByValue(chart.metrics.options, metricId);
        var field = data.goalFields[metricId];
        return {metric: metric, field: field, index: index};
    }

    function updateCampaignGoals (chart, goals, campaignGoals) {
        var commonYAxis = true;
        goals.forEach(function (goal) {
            var metric = goal.metric;
            var goalField = goal.field;
            var legendGoal = {
                id: goalField.id,
                name: 'Goals',
            };
            addLegendItem(chart, COLORS.GOALS, legendGoal, false, goals.indexOf(goal) + 1);
            campaignGoals[goalField.id].forEach(function (data) {
                if (COMMON_Y_AXIS_METRICS.indexOf(goalField.id) === -1) {
                    commonYAxis = false;
                }
                var name = 'Goal (' + goalField.name + ')';
                var yAxis = commonYAxis ? 0 : goal.index;
                var pointFormat = getPointFormat(metric);
                addGoalSeries(chart, name, data, COLORS.GOALS[goal.index], yAxis, pointFormat);
            });
        });
    }

    function updateSeries (chart, group, metricIds) {
        var color = getColor(chart, group),
            commonYAxis = null;
        addLegendItem(chart, color, group, true);

        commonYAxis = true;
        metricIds.forEach(function (metricId) {
            if (COMMON_Y_AXIS_METRICS.indexOf(metricId) === -1) {
                commonYAxis = false;
            }
        });

        metricIds.forEach(function (metricId, index) {
            var metric = zemChartMetricsService.findMetricByValue(chart.metrics.options, metricId);
            if (!metric) return;

            var data = group.seriesData[metricId] || [];
            if (data.length) chart.hasData = true;

            var name = group.name + ' (' + metric.name + ')';
            var yAxis = commonYAxis ? 0 : index;
            var pointFormat = getPointFormat(metric);
            addSeries(chart, name, data, color[index], yAxis, pointFormat);
        });
    }

    function addSeries (chart, name, data, color, yAxis, format) {
        data = transformDate(data);
        data = fillGaps(data);
        chart.config.series.unshift({
            name: name,
            color: color,
            yAxis: yAxis,
            data: data,
            tooltip: {
                pointFormat: createPointFormatHTML(name, color, format)
            },
            marker: {
                radius: 3,
                symbol: 'square',
                fillColor: color,
                lineWidth: 2,
                lineColor: null
            }
        });
    }

    function addGoalSeries (chart, name, data, color, yAxis, format) {
        data = transformDate(data);
        if (!name) {
            return;
        }

        chart.config.series.push({
            name: name,
            color: color,
            yAxis: yAxis,
            data: data,
            step: true,
            dashStyle: 'ShortDash',
            connectNulls: true,
            tooltip: {
                pointFormat: createPointFormatHTML(name, color, format)
            },
            marker: {
                enabled: false,
            },
        });
    }

    function createPointFormatHTML (name, color, format) {
        return '<div class="color-box" style="background-color: ' + color + '"></div>' +
            name + ': <b>' + format + '</b></br>';
    }

    /////////////
    // helpers //
    /////////////

    var getMetricFormat = function (metric) {
        return {type: metric.type, fractionSize: metric.fractionSize};
    };

    var getPointFormat = function (metric) {
        var format = getMetricFormat(metric);
        var valueSuffix = '';
        var valuePrefix = '';
        var fractionSize = 0;

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

    function updateAxisFormats (chart, metricIds) {
        var format = null;
        var axisFormat = null;

        metricIds.forEach(function (metricId, index) {
            var metric = zemChartMetricsService.findMetricByValue(chart.metrics.options, metricId);
            if (!metric) return;

            format = getMetricFormat(metric);
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

            chart.config.yAxis[index].labels = {
                format: axisFormat
            };
        });
    }

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

        var usedDates = {},
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

    function clearUsedColors (chart, data) {
        // clean usedColors of all groupIds that are not selected anymore
        var groupId = null;
        var groupIds = data.map(function (group) {
            return group.id.toString();
        });

        for (groupId in chart.legend.usedColors) {
            if (!chart.legend.usedColors.hasOwnProperty(groupId)) {
                continue;
            }

            if (groupIds.indexOf(groupId.toString()) === -1) {
                delete chart.legend.usedColors[groupId];
            }
        }
    }

    var getColor = function (chart, group) {
        var color = null;
        var usedColorIndexes = null;
        var i = 0;

        if (group.id === 'totals') {
            return COLORS.TOTALS;
        }

        // check if group had been assigned a color before
        color = COLORS.DATA[chart.legend.usedColors[group.id]];

        // if not, select one of the available colors
        if (!color) {
            usedColorIndexes = Object.keys(chart.legend.usedColors).map(function (key) {
                return chart.legend.usedColors[key];
            });

            for (i = 0; i < COLORS.DATA.length; i++) {
                if (usedColorIndexes.indexOf(i) !== -1) {
                    continue;
                }

                color = COLORS.DATA[i];
                chart.legend.usedColors[group.id] = i;
                break;
            }
        }

        return color;
    };

    var addLegendItem = function (chart, color, group, removable, index) {
        if (index === undefined) {
            index = chart.legend.items.length;
        }
        var legendItem = {
            id: group.id,
            name: group.name,
            color1: color[0],
            color2: color[1],
            removable: removable,
        };


        if (legendItem.id === 'totals') {
            chart.legend.items.unshift(legendItem);
        } else {
            var exists = false;
            chart.legend.items.forEach(function (legendItem) {
                if (legendItem.name === group.name) {
                    exists = true;
                }
            });
            if (!exists) {
                chart.legend.items.splice(index, 0, legendItem);
            }
        }
    };
});
