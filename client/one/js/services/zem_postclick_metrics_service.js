/*globals angular,oneApp,options,moment*/
"use strict";

oneApp.factory('zemPostclickMetricsService', function() {
    function insertAcquisitionColumns(columns, position, isShown, isInternal) {
        columns.splice(position, 0, {
            name: 'Visits',
            field: 'visits',
            checked: true,
            type: 'number',
            shown: isShown,
            internal: isInternal,
            help: 'Total number of sessions within a date range. A session is the period of time in which a user is actively engaged with your site.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        }, {
            name: 'Click Discrepancy',
            field: 'click_discrepancy',
            checked: false,
            type: 'percent',
            shown: isShown,
            internal: isInternal,
            help: 'Clicks detected only by media source as a percentage of total clicks.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        }, {
            name: 'Pageviews',
            field: 'pageviews',
            checked: true,
            type: 'number',
            shown: isShown,
            internal: isInternal,
            help: 'Total number of pageviews made during the selected date range. A pageview is a view of a single page. Repeated views are counted.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        });
    }

    function insertEngagementColumns(columns, position, isShown, isInternal) {
        columns.splice(position, 0, {
            name: '% New Users',
            field: 'percent_new_users',
            checked: false,
            type: 'percent',
            shown: isShown,
            internal: isInternal,
            help: 'An estimate of first time visits during the selected date range.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        }, {
            name: 'Bounce Rate',
            field: 'bounce_rate',
            checked: false,
            type: 'percent',
            shown: isShown,
            internal: isInternal,
            help: 'Percantage of visits that resulted in only one page view.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        }, {
            name: 'PV/Visit',
            field: 'pv_per_visit',
            checked: false,
            type: 'number',
            fractionSize: 2,
            shown: isShown,
            internal: isInternal,
            help: 'Average number of pageviews per visit.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        }, {
            name: 'Avg. ToS',
            field: 'avg_tos',
            checked: false,
            type: 'seconds',
            shown: isShown,
            internal: isInternal,
            help: 'Average time spent on site in seconds during the selected date range.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        });
    }

    function insertConversionGoalColumns(columns, position, isShown, isInternal) {
        columns.splice(position, 0, {
            name: 'Conversion Goal 1',
            field: 'conversion_goal_1',
            checked: false,
            type: 'number',
            help: 'Number of completions of the conversion goal',
            shown: false,
            internal: isInternal,
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        }, {
            name: 'Conversion Goal 2',
            field: 'conversion_goal_2',
            checked: false,
            type: 'number',
            help: 'Number of completions of the conversion goal',
            shown: false,
            internal: isInternal,
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        });
    }

    function concatAcquisitionChartOptions(chartOptions, isInternal) {
        return concatChartOptions(
            chartOptions,
            options.adGroupAcquisitionChartPostClickMetrics,
            isInternal,
            false
        );
    }

    function concatEngagementChartOptions(chartOptions, isInternal) {
        return concatChartOptions(
            chartOptions,
            options.adGroupEngagementChartPostClickMetrics,
            isInternal,
            false
        );
    }

    function concatChartOptions(chartOptions, newOptions, isInternal, isHidden) {
        return chartOptions.concat(newOptions.map(function (option) {
            option.internal = isInternal;
            options.hidden = isHidden;
            return option;
        }));
    }

    function getValidChartMetrics(chartMetric1, chartMetric2, conversionGoals) {
        conversionGoals = conversionGoals || [];
        var cg1Exists = conversionGoals.some(function (conversionGoal) {
            return conversionGoal.id === constants.chartMetric.CONVERSION_GOAL1;
        });

        var cg2Exists = conversionGoals.some(function (conversionGoal) {
            return conversionGoal.id === constants.chartMetric.CONVERSION_GOAL2;
        });

        if ((chartMetric1 === constants.chartMetric.CONVERSION_GOAL1 && !cg1Exists) ||
            (chartMetric1 === constants.chartMetric.CONVERSION_GOAL2 && !cg2Exists)) {
            chartMetric1 = constants.chartMetric.CLICKS;
        }

        if ((chartMetric2 === constants.chartMetric.CONVERSION_GOAL1 && !cg1Exists) ||
            (chartMetric2 === constants.chartMetric.CONVERSION_GOAL2 && !cg2Exists)) {
            chartMetric2 = constants.chartMetric.IMPRESSIONS;
        }

        return {
            chartMetric1: chartMetric1,
            chartMetric2: chartMetric2
        };
    }

    function setConversionGoalChartOptions(chartOptions, conversionGoals, isShown) {
        if (!conversionGoals || !conversionGoals.length) {
            return chartOptions;
        }

        var newOptions = angular.copy(chartOptions);
        conversionGoals.forEach(function(el, ix) {
            for (var i = 0; i < newOptions.length; i++) {
                if (newOptions[i].value === el.id) {
                    newOptions[i].name = el.name;
                    newOptions[i].shown = isShown;
                }
            }
        });
        return newOptions;
    }

    function setConversionGoalColumnsDefaults(cols, conversionGoals, isShown) {
        if (!conversionGoals || !conversionGoals.length) {
            return cols;
        }

        var newCols = angular.copy(cols);
        conversionGoals.forEach(function(el, ix) {
            for (var i = 0; i < newCols.length; i++) {
                if (newCols[i].field === el.id) {
                    newCols[i].name = el.name;
                    newCols[i].shown = isShown;
                }
            }
        });
        return newCols;
    }

    return {
        insertAcquisitionColumns: insertAcquisitionColumns,
        insertEngagementColumns: insertEngagementColumns,
        insertConversionGoalColumns: insertConversionGoalColumns,
        concatAcquisitionChartOptions: concatAcquisitionChartOptions,
        concatEngagementChartOptions: concatEngagementChartOptions,
        concatChartOptions: concatChartOptions,
        getValidChartMetrics: getValidChartMetrics,
        setConversionGoalChartOptions: setConversionGoalChartOptions,
        setConversionGoalColumnsDefaults: setConversionGoalColumnsDefaults
    };
});
