/* globals oneApp */
'use strict';

oneApp.factory('zemOptimisationMetricsService', function () {
    function insertAudienceOptimizationColumns (columns, position, isShown, isInternal) {
        isShown = false;
        columns.splice(position, 0, {
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
        }, {
            name: 'Unbounced Visitors',
            field: 'unbounced_visits',
            checked: false,
            type: 'number',
            shown: isShown,
            internal: isInternal,
            help: 'Percent of visitors that navigate to more than one page on the site.',
            totalRow: true,
            order: true,
            initialOrder: 'desc',
        }, {
            name: 'Total Pageviews',
            field: 'total_pageviews',
            checked: true,
            type: 'number',
            shown: isShown,
            internal: isInternal,
            help: 'Total pageviews.',
            totalRow: true,
            order: true,
            initialOrder: 'desc',
        }, {
            name: 'Avg. Cost Per Second',
            field: 'avg_cost_per_second',
            checked: true,
            type: 'currency',
            shown: isShown,
            internal: isInternal,
            help: 'Average cost per time spent on site.',
            totalRow: true,
            order: true,
            initialOrder: 'desc',
        }, {
            name: 'Avg. Cost Per Pageview',
            field: 'avg_cost_per_pageview',
            checked: true,
            type: 'currency',
            shown: isShown,
            internal: isInternal,
            help: 'Average cost per pageview.',
            totalRow: true,
            order: true,
            initialOrder: 'desc',
        }, {
            name: 'Avg. Cost For Unbounced Visitor',
            field: 'avg_cost_per_non_bounced_visitor',
            checked: true,
            type: 'currency',
            shown: isShown,
            internal: isInternal,
            help: 'Average cost per non-bounced visitors.',
            totalRow: true,
            order: true,
            initialOrder: 'desc',
        }, {
            name: 'Avg. Cost For New Visitor',
            field: 'avg_cost_for_new_visitor',
            checked: true,
            type: 'currency',
            shown: isShown,
            internal: isInternal,
            help: 'Average cost for new visitor.',
            totalRow: true,
            order: true,
            initialOrder: 'desc',
        });

        for (var i = 0; i < 5; i++) {
            columns.splice(position + i + 6, 0, {
                name: 'Avg. cost per conversion',
                field: 'avg_cost_per_conversion_goal_' + i,
                checked: true,
                type: 'currency',
                shown: isShown,
                internal: isInternal,
                help: 'Cost per acquisition.',
                totalRow: true,
                order: true,
                initialOrder: 'desc',
            });
        }
    }

    function columnCategories () {
        var categories = {
            total_seconds: true,
            unbounced_visits: true,
            total_pageviews: true,
            avg_cost_per_second: true,
            avg_cost_per_pageview: true,
            avg_cost_per_non_bounced_visitor: true,
            avg_cost_for_new_visitor: true,
            cpa: true,
        };
        for (var i = 0; i < 5; i++) {
            categories['avg_cost_per_conversion_goal_' + i] = true;
        }
        return categories;
    }

    function createColumnCategories () {
        var columnCats = columnCategories();
        return {
            'name': 'Campaign Goals',
            'fields': Object.keys(columnCats),
        };
    }

    function updateVisibility (columns, goals) {
        var columnCats = columnCategories();
        columns.forEach(function (column) {
            if (!columnCats[column.field]) {
                return;
            }

            if (columnCats[column.field]) {
                column.shown = false;
                column.unselectable = true;
            }

            if (goals === undefined) {
                return;
            }

            goals.forEach(function (goal) {
                if (goal.fields[column.field] === undefined) {
                    return;
                }
                column.shown = true;
                column.unselectable = false;

                if (goal.conversion) {
                    column.name = goal.name + ' (' + goal.conversion + ')';
                }
            });
        });
    }

    function concatChartOptions (goals, chartOptions, newOptions, isInternal) {
        return chartOptions.concat(newOptions.map(function (option) {
            option.internal = isInternal;
            option.shown = false;
            return option;
        }));
    }

    function updateChartOptionsVisibility (chartOptions, goals) {
        var columnCats = columnCategories();
        chartOptions.forEach(function (option) {
            if (!columnCats[option.value]) {
                return;
            }

            if (columnCats[option.value]) {
                option.shown = false;
            }

            (goals || []).forEach(function (goal) {
                if (goal.fields[option.value] === undefined) {
                    return;
                }
                option.shown = true;
                if (goal.conversion) {
                    option.name = goal.name + ' (' + goal.conversion + ')';
                }
            });
        });
    }

    return {
        createColumnCategories: createColumnCategories,
        insertAudienceOptimizationColumns: insertAudienceOptimizationColumns,
        updateVisibility: updateVisibility,
        concatChartOptions: concatChartOptions,
        updateChartOptionsVisibility: updateChartOptionsVisibility,
    };
});
