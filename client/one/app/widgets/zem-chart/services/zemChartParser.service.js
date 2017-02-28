angular.module('one.widgets').service('zemChartParser', function (zemChartMetricsService) {

    var COMMON_Y_AXIS_METRICS = ['clicks', 'visits', 'pageviews'];
    var TOTALS_COLORS = ['#3f547f', '#b2bbcc'];
    var GOALS_COLORS = ['#99cc00', '#d6eb99'];
    var DATA_COLORS = [
        ['#29aae3', '#a9ddf4'],
        ['#0aaf9f', '#9ddfd9'],
        ['#f15f74', '#f9bfc7'],
    ];

    this.parseMetaData = parseMetaData;
    this.parseData = parseData;

    function parseMetaData (chart, metaData) {
        chart.metrics.options = metaData.metrics;
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
            for (i = 0; i < chart.config.options.yAxis.length; i++) {
                chart.config.options.yAxis[i].max = 10;
            }
        } else {
            for (i = 0; i < chart.config.options.yAxis.length; i++) {
                chart.config.options.yAxis[i].max = null;
            }
        }
    }

    function updateDateRange (chart, dateRange) {
        // Set min and max only if start date and end date are different. If
        // they are the same, let charts figure it out because otherwise it
        // renders strangely.
        if (dateRange.startDate.valueOf() !== dateRange.endDate.valueOf()) {
            chart.config.options.xAxis.min = moment(dateRange.startDate)
            .add(dateRange.startDate.utcOffset(), 'minutes')
            .valueOf();
            chart.config.options.xAxis.max = moment(dateRange.endDate)
            .add(dateRange.endDate.utcOffset(), 'minutes')
            .valueOf();
        } else {
            chart.config.options.xAxis.min = null;
            chart.config.options.xAxis.max = null;
        }
    }

    function applyGoals (chart, data, metrics) {
        if (!data.campaignGoals || !data.goalFields) {
            return;
        }

        var goal1 = data.goalFields[metrics[0]];
        var goal2 = data.goalFields[metrics[1]];
        var metricIds = [];

        if (goal1 && metrics[0] && data.campaignGoals[goal1.id]) {
            metricIds.push(metrics[0]);
        }

        if (goal2 && metrics[1] && data.campaignGoals[goal2.id]) {
            if (metrics[0] !== metrics[1]) {
                metricIds.push(metrics[1]);
            }
        }
        updateCampaignGoals(chart, metricIds, data.campaignGoals, data.goalFields);
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
            var data = group.seriesData[metricId] || [];
            if (data.length) chart.hasData = true;

            var metric = zemChartMetricsService.findMetricByValue(chart.metrics.options, metricId);
            var name = group.name + ' (' + metric.name + ')';
            var yAxis = commonYAxis ? 0 : index;
            var pointFormat = getPointFormat(metric);
            addSeries(chart, name, data, color[index], yAxis, pointFormat);
        });
    }

    function updateCampaignGoals (chart, metricIds, campaignGoals, fieldGoalMap) {
        var index = 0;
        var commonYAxis = true;
        metricIds.forEach(function (metricId) {
            var metric = zemChartMetricsService.findMetricByValue(chart.metrics.options, metricId);
            var goal = fieldGoalMap[metricId],
                legendGoal = {
                    id: goal.id,
                    name: 'Goals',
                },
                colors = GOALS_COLORS;
            addLegendItem(chart, colors, legendGoal, false, metricIds.indexOf(metricId) + 1);
            campaignGoals[goal.id].forEach(function (data) {
                if (COMMON_Y_AXIS_METRICS.indexOf(metricId) === -1) {
                    commonYAxis = false;
                }
                var name = 'Goal (' + goal.name + ')';
                var yAxis = commonYAxis ? 0 : index;
                var pointFormat = getPointFormat(metric);
                addGoalSeries(chart, name, data, colors[index], yAxis, pointFormat);
            });

            index += 1;
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
            format = getMetricFormat(zemChartMetricsService.findMetricByValue(chart.metrics.options, metricId));
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

            chart.config.options.yAxis[index].labels = {
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
            return TOTALS_COLORS;
        }

        // check if group had been assigned a color before
        color = DATA_COLORS[chart.legend.usedColors[group.id]];

        // if not, select one of the available colors
        if (!color) {
            usedColorIndexes = Object.keys(chart.legend.usedColors).map(function (key) {
                return chart.legend.usedColors[key];
            });

            for (i = 0; i < DATA_COLORS.length; i++) {
                if (usedColorIndexes.indexOf(i) !== -1) {
                    continue;
                }

                color = DATA_COLORS[i];
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
