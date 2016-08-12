/* globals oneApp,options,constants,angular */
'use strict';

oneApp.factory('zemPostclickMetricsService', function () {
    function insertAcquisitionColumns (columns, position, isShown, isInternal) {
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
            initialOrder: 'desc',
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
            initialOrder: 'desc',
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
            initialOrder: 'desc',
        });
    }

    function insertEngagementColumns (columns, position, isShown, isInternal) {
        columns.splice(
            position,
            0,
            {
                name: 'Unique Users',
                field: 'unique_users',
                checked: false,
                type: 'number',
                shown: isShown,
                internal: isInternal,
                help: 'The total number of unique people who visited your site.',
                totalRow: true,
                order: true,
                initialOrder: 'desc',
            },
            {
                name: 'New Users',
                field: 'new_users',
                checked: false,
                type: 'number',
                shown: isShown,
                internal: isInternal,
                help: 'The total number of unique people who visited your site for the first time.',
                totalRow: true,
                order: true,
                initialOrder: 'desc',
            },
            {
                name: 'Returning Users',
                field: 'returning_users',
                checked: false,
                type: 'number',
                shown: isShown,
                internal: isInternal,
                help: 'The total number of unique people who already visited your site in the past.',
                totalRow: true,
                order: true,
                initialOrder: 'desc',
            },
            {
                name: '% New Users',
                field: 'percent_new_users',
                checked: false,
                type: 'percent',
                shown: isShown,
                internal: isInternal,
                help: 'An estimate of first time visits during the selected date range.',
                totalRow: true,
                order: true,
                initialOrder: 'desc',
            },
            {
                name: 'Pageviews per Visit',
                field: 'pv_per_visit',
                checked: false,
                type: 'number',
                fractionSize: 2,
                shown: isShown,
                internal: isInternal,
                help: 'Average number of pageviews per visit.',
                totalRow: true,
                order: true,
                initialOrder: 'desc',
            },
            {
                name: 'Bounced Visits',
                field: 'bounced_visits',
                checked: false,
                type: 'number',
                shown: isShown,
                internal: isInternal,
                help: 'The total number of visits in which people left your site without interacting with the page.',
                totalRow: true,
                order: true,
                initialOrder: 'desc',
            },
            {
                name: 'Non-Bounced Visits',
                field: 'non_bounced_visits',
                checked: true,
                type: 'number',
                shown: isShown,
                internal: isInternal,
                help: 'Number of visitors that navigate to more than one page on the site.',
                totalRow: true,
                order: true,
                initialOrder: 'desc',
            },
            {
                name: 'Bounce Rate',
                field: 'bounce_rate',
                checked: false,
                type: 'percent',
                shown: isShown,
                internal: isInternal,
                help: 'Percentage of visits that resulted in only one page view.',
                totalRow: true,
                order: true,
                initialOrder: 'desc',
            },
            {
                name: 'Total Seconds',
                field: 'total_seconds',
                checked: true,
                type: 'number',
                shown: isShown,
                internal: isInternal,
                help: 'Total time spend on site.',
                totalRow: true,
                order: true,
                initialOrder: 'desc',
            },
            {
                name: 'Time on Site',
                field: 'avg_tos',
                checked: false,
                type: 'seconds',
                shown: isShown,
                internal: isInternal,
                help: 'Average time spent on site in seconds during the selected date range.',
                totalRow: true,
                order: true,
                initialOrder: 'desc',
            }
        );
    }

    function insertConversionGoalColumns (columns, position, isShown, isInternal) {
        for (var i = 15; i > 0; i--) {
            columns.splice(position, 0, {
                name: 'Conversion Goal ' + i,
                field: 'conversion_goal_' + i,
                checked: false,
                type: 'number',
                help: 'Number of completions of the conversion goal',
                shown: false,
                internal: isInternal,
                totalRow: true,
                order: true,
                initialOrder: 'desc',
            });
        }
    }

    function concatAcquisitionChartOptions (chartOptions, isInternal) {
        return concatChartOptions(
            chartOptions,
            options.adGroupAcquisitionChartPostClickMetrics,
            isInternal,
            false
        );
    }

    function concatEngagementChartOptions (chartOptions, isInternal) {
        return concatChartOptions(
            chartOptions,
            options.adGroupEngagementChartPostClickMetrics,
            isInternal,
            false
        );
    }

    function concatChartOptions (chartOptions, newOptions, isInternal, isHidden) {
        return chartOptions.concat(newOptions.map(function (option) {
            option = angular.extend({}, option);
            option.internal = isInternal;
            option.hidden = isHidden;
            return option;
        }));
    }

    function getValidChartMetrics (chartMetric1, chartMetric2, conversionGoals) {
        conversionGoals = conversionGoals || [];

        var cgIds = conversionGoals.map(function (conversionGoal) {
            return conversionGoal.id;
        });

        var cgChartMetrics = [
            constants.chartMetric.CONVERSION_GOAL1,
            constants.chartMetric.CONVERSION_GOAL2,
            constants.chartMetric.CONVERSION_GOAL3,
            constants.chartMetric.CONVERSION_GOAL4,
            constants.chartMetric.CONVERSION_GOAL5,
            constants.chartMetric.CONVERSION_GOAL6,
            constants.chartMetric.CONVERSION_GOAL7,
            constants.chartMetric.CONVERSION_GOAL8,
            constants.chartMetric.CONVERSION_GOAL9,
            constants.chartMetric.CONVERSION_GOAL10,
            constants.chartMetric.CONVERSION_GOAL11,
            constants.chartMetric.CONVERSION_GOAL12,
            constants.chartMetric.CONVERSION_GOAL13,
            constants.chartMetric.CONVERSION_GOAL14,
            constants.chartMetric.CONVERSION_GOAL15,
        ];

        if (cgChartMetrics.indexOf(chartMetric1) > -1 && cgIds.indexOf(chartMetric1) === -1) {
            chartMetric1 = constants.chartMetric.CLICKS;
        }

        if (cgChartMetrics.indexOf(chartMetric2) > -1 && cgIds.indexOf(chartMetric2) === -1) {
            chartMetric2 = constants.chartMetric.IMPRESSIONS;
        }

        return {
            chartMetric1: chartMetric1,
            chartMetric2: chartMetric2,
        };
    }

    function setConversionGoalChartOptions (chartOptions, conversionGoals) {
        if (!conversionGoals || !conversionGoals.length) {
            return;
        }

        conversionGoals.forEach(function (el, ix) {
            for (var i = 0; i < chartOptions.length; i++) {
                if (chartOptions[i].value === el.id) {
                    chartOptions[i].name = el.name;
                    chartOptions[i].shown = true;
                }
            }
        });
    }

    function setConversionGoalColumnsDefaults (cols, conversionGoals) {
        if (!conversionGoals || !conversionGoals.length) {
            return;
        }

        conversionGoals.forEach(function (el, ix) {
            for (var i = 0; i < cols.length; i++) {
                if (cols[i].field === el.id) {
                    cols[i].name = el.name;
                    cols[i].shown = true;
                }
            }
        });
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
