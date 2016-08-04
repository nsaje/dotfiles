/* globals oneApp,angular */
'use strict';

oneApp.factory('zemOptimisationMetricsService', function () {
    function insertAudienceOptimizationColumns (columns, position, isShown, isInternal) {
        columns.splice(position, 0, {
            name: 'Avg. Cost per Minute',
            field: 'avg_cost_per_minute',
            checked: true,
            type: 'currency',
            shown: isShown,
            internal: isInternal,
            help: 'Average cost per minute spent on site.',
            totalRow: true,
            order: true,
            initialOrder: 'desc',
        }, {
            name: 'Avg. Cost per Pageview',
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
            name: 'Avg. Cost per Visit',
            field: 'avg_cost_per_visit',
            checked: true,
            type: 'currency',
            shown: isShown,
            internal: isInternal,
            help: 'Average cost per visit.',
            totalRow: true,
            order: true,
            initialOrder: 'desc',
        }, {
            name: 'Avg. Cost per Non-Bounced Visit',
            field: 'avg_cost_per_non_bounced_visit',
            checked: true,
            type: 'currency',
            shown: isShown,
            internal: isInternal,
            help: 'Average cost per non-bounced visit.',
            totalRow: true,
            order: true,
            initialOrder: 'desc',
        }, {
            name: 'Avg. Cost for New Visitor',
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

        for (var i = 0; i < 16; i++) {
            columns.splice(position + i + 6, 0, {
                name: 'Avg. CPA',
                field: 'avg_cost_per_conversion_goal_' + i,
                checked: true,
                type: 'currency',
                shown: false,
                internal: isInternal,
                help: 'Average cost per acquisition.',
                totalRow: true,
                order: true,
                initialOrder: 'desc',
            });
        }
    }

    function columnCategories () {
        var categories = {
            avg_cost_per_minute: false,  // add to category but don't hide column
            avg_cost_per_pageview: false,
            avg_cost_per_non_bounced_visit: false,
            avg_cost_for_new_visitor: false,
            avg_cost_per_visit: false,
            cpa: true,
        };
        for (var i = 0; i < 16; i++) {
            categories['avg_cost_per_conversion_goal_' + i] = true;
        }
        return categories;
    }

    function createColumnCategories () {
        var columnCats = columnCategories();
        return {
            'name': 'Goals',
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
            option = angular.extend({}, option);
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
