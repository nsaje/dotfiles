/* globals options,constants,angular */
'use strict';

angular.module('one.legacy').factory('zemPostclickMetricsService', function () {
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

    function insertAudienceOptimizationColumns (columns, position) {
        columns.splice(position, 0, {
            name: 'Avg. Cost per Minute',
            field: 'avg_cost_per_minute',
            checked: true,
            type: 'currency',
            shown: true,
            internal: false,
            help: 'Average cost per minute spent on site.',
            totalRow: true,
            order: true,
            initialOrder: 'desc',
        }, {
            name: 'Avg. Cost per Pageview',
            field: 'avg_cost_per_pageview',
            checked: true,
            type: 'currency',
            shown: true,
            internal: false,
            help: 'Average cost per pageview.',
            totalRow: true,
            order: true,
            initialOrder: 'desc',
        }, {
            name: 'Avg. Cost per Visit',
            field: 'avg_cost_per_visit',
            checked: true,
            type: 'currency',
            shown: true,
            internal: false,
            help: 'Average cost per visit.',
            totalRow: true,
            order: true,
            initialOrder: 'desc',
        }, {
            name: 'Avg. Cost per Non-Bounced Visit',
            field: 'avg_cost_per_non_bounced_visit',
            checked: true,
            type: 'currency',
            shown: true,
            internal: false,
            help: 'Average cost per non-bounced visit.',
            totalRow: true,
            order: true,
            initialOrder: 'desc',
        }, {
            name: 'Avg. Cost for New Visitor',
            field: 'avg_cost_for_new_visitor',
            checked: true,
            type: 'currency',
            shown: true,
            internal: false,
            help: 'Average cost for new visitor.',
            totalRow: true,
            order: true,
            initialOrder: 'desc',
        }, {
            field: 'conversion_goals_avg_cost_placeholder',
            shown: false,
        }, {
            field: 'pixels_avg_cost_placeholder',
            shown: false,
        });
    }


    function insertConversionsPlaceholders (columns, position) {
        columns.splice(
            position,
            0,
            {
                field: 'conversion_goals_placeholder',
                shown: false,
            },
            {
                field: 'pixels_placeholder',
                shown: false,
            }
        );
    }

    function insertCPAPlaceholders (columns, position) {
        columns.splice(
            position,
            0,
            {
                field: 'conversion_goals_avg_cost_placeholder',
                shown: false,
            },
            {
                field: 'pixels_avg_cost_placeholder',
                shown: false,
            }
        );
    }

    function insertIntoColumns (columns, newColumns, placeholder) {
        var columnPosition = findColumnPosition(columns, placeholder);
        if (!columnPosition) return;

        Array.prototype.splice.apply(columns, [columnPosition, 0].concat(newColumns));
    }

    function insertIntoCategories (categories, newFields, placeholder) {
        var categoryPosition = findCategoryPosition(categories, placeholder);
        if (!categoryPosition) return;

        Array.prototype.splice.apply(categoryPosition.fields, [categoryPosition.position, 0].concat(newFields));
    }

    function setColumns (columns, categories, newColumns, placeholder) {
        // add dynamic columns and category fields to position after placeholder
        var newFields = newColumns.map(function (column) {
            return column.field;
        });

        insertIntoColumns(columns, newColumns, placeholder);
        insertIntoCategories(categories, newFields, placeholder);
    }

    function insertPixelColumns (columns, categories, pixels) {
        if (!pixels) return;

        var newColumns = [],
            newAvgCostColumns = [];
        angular.forEach(pixels, function (pixel) {
            angular.forEach(options.conversionWindows, function (window) {
                var name = pixel.name + ' ' + window.name,
                    field = pixel.prefix + '_' + window.value;
                newColumns.push({
                    name: name,
                    field: field,
                    type: 'number',
                    help: 'Number of completions of the conversion goal',
                    shown: true,
                    checked: false,
                    internal: false,
                    totalRow: true,
                    order: true,
                    initialOrder: 'desc',
                });

                newAvgCostColumns.push({
                    name: 'CPA (' + name + ')',
                    field: 'avg_cost_per_' + field,
                    type: 'currency',
                    help: 'Average cost per acquisition.',
                    shown: true,
                    checked: false,
                    internal: false,
                    totalRow: true,
                    order: true,
                    initialOrder: 'desc',
                });
            });
        });

        setColumns(columns, categories, newColumns, 'pixels_placeholder');
        setColumns(columns, categories, newAvgCostColumns, 'pixels_avg_cost_placeholder');
    }

    function insertConversionGoalColumns (columns, categories, conversionGoals) {
        if (!conversionGoals) return;

        var newColumns = [],
            newAvgCostColumns = [];
        angular.forEach(conversionGoals, function (goal) {
            newColumns.push({
                name: goal.name,
                field: goal.id,
                type: 'number',
                help: 'Number of completions of the conversion goal',
                shown: true,
                internal: false,
                totalRow: true,
                order: true,
                initialOrder: 'desc',
            });

            newAvgCostColumns.push({
                name: 'CPA (' + goal.name + ')',
                field: 'avg_cost_per_' + goal.id,
                type: 'currency',
                shown: true,
                internal: false,
                help: 'Average cost per acquisition.',
                totalRow: true,
                order: true,
                initialOrder: 'desc',
            });
        });

        setColumns(columns, categories, newColumns, 'conversion_goals_placeholder');
        setColumns(columns, categories, newAvgCostColumns, 'conversion_goals_avg_cost_placeholder');
    }

    function findCategoryPosition (categories, field) {
        for (var i = 0; i < categories.length; i++) {
            for (var j = 0; j < categories[i].fields.length; j++) {
                if (categories[i].fields[j] === field) {
                    return {
                        fields: categories[i].fields,
                        position: j + 1 // return next index
                    };
                }
            }
        }
    }

    function findColumnPosition (columns, field) {
        for (var i = 0; i < columns.length; i++) {
            if (columns[i].field === field) {
                // return next index
                return i + 1;
            }
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

    function findChartOptionPosition (chartOptions, field) {
        for (var i = 0; i < chartOptions.length; i++) {
            if (chartOptions[i].value === field) {
                // return next index
                return i + 1;
            }
        }
    }

    function insertConversionsGoalChartOptions (chartOptions, conversionGoals) {
        if (!conversionGoals) return;

        var newOptions = [],
            newGoalsOptions = [];
        angular.forEach(conversionGoals, function (goal) {
            newOptions.push({
                value: goal.id,
                name: goal.name,
            });

            newGoalsOptions.push({
                value: 'avg_cost_per_' + goal.id,
                name: 'CPA (' + goal.name + ')',
            });
        });
        var conversionsPosition = findChartOptionPosition(chartOptions, constants.chartMetric.CONVERSION_GOALS_PLACEHOLDER);
        Array.prototype.splice.apply(chartOptions, [conversionsPosition, 0].concat(newOptions));

        var goalsPosition = findChartOptionPosition(chartOptions, constants.chartMetric.CONVERSION_GOALS_AVG_COST_PLACEHOLDER);
        Array.prototype.splice.apply(chartOptions, [goalsPosition, 0].concat(newGoalsOptions));
    }

    function insertPixelChartOptions (chartOptions, pixels) {
        if (!pixels) return;

        var newOptions = [],
            newGoalsOptions = [];
        angular.forEach(pixels, function (pixel) {
            angular.forEach(options.conversionWindows, function (window) {
                var name = pixel.name + ' ' + window.name,
                    field = pixel.prefix + '_' + window.value;
                newOptions.push({
                    value: field,
                    name: name,
                });

                newGoalsOptions.push({
                    value: 'avg_cost_per_' + field,
                    name: 'CPA (' + name + ')',
                });
            });
        });
        var conversionsPosition = findChartOptionPosition(chartOptions, constants.chartMetric.PIXELS_PLACEHOLDER);
        Array.prototype.splice.apply(chartOptions, [conversionsPosition, 0].concat(newOptions));

        var goalsPosition = findChartOptionPosition(chartOptions, constants.chartMetric.PIXELS_AVG_COST_PLACEHOLDER);
        Array.prototype.splice.apply(chartOptions, [goalsPosition, 0].concat(newGoalsOptions));
    }

    function getValidChartMetrics (chartMetric1, chartMetric2, chartMetricOptions) {
        var values = chartMetricOptions.filter(function (option) {
            return !option.placeholder;
        }).map(function (option) {
            return option.value;
        });

        if (!chartMetric1 || !values || values.indexOf(chartMetric1) < 0) {
            chartMetric1 = constants.chartMetric.CLICKS;
        }
        if (!chartMetric2 || !values || values.indexOf(chartMetric2) < 0) {
            chartMetric2 = constants.chartMetric.IMPRESSIONS;
        }

        return {
            metric1: chartMetric1,
            metric2: chartMetric2,
        };
    }

    return {
        insertAudienceOptimizationColumns: insertAudienceOptimizationColumns,
        insertAcquisitionColumns: insertAcquisitionColumns,
        insertEngagementColumns: insertEngagementColumns,
        insertConversionGoalColumns: insertConversionGoalColumns,
        insertPixelColumns: insertPixelColumns,
        insertConversionsPlaceholders: insertConversionsPlaceholders,
        insertCPAPlaceholders: insertCPAPlaceholders,
        concatAcquisitionChartOptions: concatAcquisitionChartOptions,
        concatEngagementChartOptions: concatEngagementChartOptions,
        concatChartOptions: concatChartOptions,
        insertPixelChartOptions: insertPixelChartOptions,
        insertConversionsGoalChartOptions: insertConversionsGoalChartOptions,
        getValidChartMetrics: getValidChartMetrics,
    };
});
