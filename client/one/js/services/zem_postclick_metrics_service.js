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

    function concatAcquisitionChartOptions(chartOptions, isInternal) {
        return concatChartOptions(
            chartOptions,
            options.adGroupAcquisitionChartPostClickMetrics,
            isInternal
        );
    }

    function concatEngagementChartOptions(chartOptions, isInternal) {
        return concatChartOptions(
            chartOptions,
            options.adGroupEngagementChartPostClickMetrics,
            isInternal
        );
    }

    function concatChartOptions(chartOptions, postclickOptions, isInternal) {
        return chartOptions.concat(postclickOptions.map(function (option) {
            option.internal = isInternal;
            return option;
        }));
    }

    function insertGoalColumns(columns, position, rows, postclickCategory, isInternal) {
        for(var i = 0; i < rows.length; i++) {
            for(var field in rows[i]) {
                if(columnsContainField(columns, field)) {
                    continue;
                }

                if(field.indexOf(': Conversions') != -1) {
                    var columnDescription = {
                        name: field.substr('goal__'.length),
                        field: field,
                        checked: false,
                        type: 'number',
                        help: 'Number of completions of the conversion goal',
                        internal: isInternal,
                        totalRow: true,
                        order: true,
                        initialOrder: 'desc',
                        shown: true
                    };
                    columns.splice(position, 0, columnDescription);
                    postclickCategory.fields.push(columnDescription.field);
                } else if(field.indexOf(': Conversion Rate') != -1) {
                    var columnDescription = {
                        name: field.substr('goal__'.length),
                        field: field,
                        checked: false,
                        type: 'percent',
                        help: 'Percentage of visits which resulted in a goal completion',
                        internal: isInternal,
                        totalRow: true,
                        order: true,
                        initialOrder: 'desc',
                        shown: true
                    };
                    columns.splice(position, 0, columnDescription);
                    postclickCategory.fields.push(columnDescription.field);
                }
            }
        }
    };

    function columnsContainField(columns, field) {
        for(var i = 0; i < columns.length; i++) {
            if(field == columns[i]['field']){
                return true;
            }
        }
        return false;
    };

    return {
        insertAcquisitionColumns: insertAcquisitionColumns,
        insertEngagementColumns: insertEngagementColumns,
        concatAcquisitionChartOptions: concatAcquisitionChartOptions,
        concatEngagementChartOptions: concatEngagementChartOptions,
        insertGoalColumns: insertGoalColumns
    }
});
