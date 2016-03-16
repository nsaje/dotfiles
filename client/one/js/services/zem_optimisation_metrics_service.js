/* globals oneApp */
'use strict';

oneApp.factory('zemOptimisationMetricsService', function () {
    function insertAudienceOptimizationColumns (columns, position, isShown, isInternal) {
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
            type: 'percent',
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
            name: 'Avg. Cost For Non-bounced Visitor',
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
            name: 'CPA',
            field: 'cpa',
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

    function createColumnCategories () {
        return {
            'name': 'Campaign Goals',
            'fields': [
                'total_seconds',
                'unbounced_visits',
                'total_pageviews',
                'avg_cost_per_second',
                'avg_cost_per_pageview',
                'avg_cost_per_non_bounced_visitor',
                'cpa',
            ],
        };
    }

    return {
        createColumnCategories: createColumnCategories,
        insertAudienceOptimizationColumns: insertAudienceOptimizationColumns,
    };
});
