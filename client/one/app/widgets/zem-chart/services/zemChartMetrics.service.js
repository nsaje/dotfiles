/* globals options,constants,angular */
'use strict';

angular.module('one.widgets').factory('zemChartMetricsService', function (zemPermissions) {
    ////////////////////////////////////////////////////////////////////////////////////
    // Definitions - Metrics, Categories
    //
    var TYPE_NUMBER = 'number';
    var TYPE_CURRENCY = 'currency';
    var TYPE_TIME = 'time';

    var COSTS_CATEGORY_NAME = 'Costs';
    var TRAFFIC_CATEGORY_NAME = 'Traffic Acquisition';
    var AUDIENCE_CATEGORY_NAME = 'Audience Metrics';
    var CONVERSIONS_CATEGORY_NAME = 'Google & Adobe Analytics Goals';
    var PIXELS_CATEGORY_NAME = 'Conversions & CPAs';

    var METRICS = { /* eslint-disable max-len */
        CLICKS: {name: 'Clicks', value: 'clicks', type: TYPE_NUMBER},
        IMPRESSIONS: {name: 'Impressions', value: 'impressions', type: TYPE_NUMBER},
        CTR: {name: 'CTR', value: 'ctr', type: 'percent', fractionSize: 2},
        CPC: {name: 'Avg. CPC', value: 'cpc', type: TYPE_CURRENCY, fractionSize: 3},
        CPM: {name: 'Avg. CMP', value: 'cpm', type: TYPE_CURRENCY, fractionSize: 3},
        DATA_COST: {name: 'Actual Data Cost', value: 'data_cost', type: TYPE_CURRENCY, fractionSize: 2, permission: 'zemauth.can_view_actual_costs'},
        MEDIA_COST: {name: 'Actual Media Cost', value: 'media_cost', type: TYPE_CURRENCY, fractionSize: 2, permission: 'zemauth.can_view_actual_costs'},
        E_DATA_COST: {name: 'Data Cost', value: 'e_data_cost', type: TYPE_CURRENCY, fractionSize: 2, permission: 'zemauth.can_view_cost_breakdown'},
        E_MEDIA_COST: {name: 'Media Cost', value: 'e_media_cost', type: TYPE_CURRENCY, fractionSize: 2, permission: 'zemauth.can_view_cost_breakdown'},
        BILLING_COST: {name: 'Total Spend', value: 'billing_cost', type: TYPE_CURRENCY, fractionSize: 2},
        LICENSE_FEE: {name: 'License Fee', value: 'license_fee', type: TYPE_CURRENCY, fractionSize: 2},
        VISITS: {name: 'Visits', value: 'visits', type: TYPE_NUMBER, permission: 'zemauth.aggregate_postclick_acquisition'},
        PAGEVIEWS: {name: 'Pageviews', value: 'pageviews', type: TYPE_NUMBER, permission: 'zemauth.aggregate_postclick_acquisition'},
        CLICK_DISCREPANCY: {name: 'Click Discrepancy', value: 'click_discrepancy', type: 'percent', fractionSize: 2, permission: 'zemauth.aggregate_postclick_acquisition'},
        PERCENT_NEW_USERS: {name: '% New Users', value: 'percent_new_users', type: 'percent', fractionSize: 2},
        RETURNING_USERS: {name: 'Returning Users', value: 'returning_users', type: TYPE_NUMBER},
        UNIQUE_USERS: {name: 'Unique Users', value: 'unique_users', type: TYPE_NUMBER},
        NEW_USERS: {name: 'New Users', value: 'unique_users', type: TYPE_NUMBER},
        BOUNCE_RATE: {name: 'Bounce Rate', value: 'bounce_rate', type: 'percent', fractionSize: 2},
        TOTAL_SECONDS: {name: 'Total Seconds', value: 'total_seconds', type: TYPE_NUMBER},
        BOUNCED_VISITS: {name: 'Bounced Visits', value: 'bounced_visits', type: TYPE_NUMBER},
        NON_BOUNCED_VISITS: {name: 'Non-Bounced Visits', value: 'non_bounced_visits', type: TYPE_NUMBER},
        PV_PER_VISIT: {name: 'Pageviews per Visit', value: 'pv_per_visit', type: TYPE_NUMBER, fractionSize: 2},
        AVG_TOS: {name: 'Time on Site', value: 'avg_tos', type: TYPE_TIME, fractionSize: 1},
        COST_PER_MINUTE: {name: 'Avg. Cost per Minute', value: 'avg_cost_per_minute', type: TYPE_CURRENCY, fractionSize: 2},
        COST_PER_PAGEVIEW: {name: 'Avg. Cost for Pageview', value: 'avg_cost_per_pageview', type: TYPE_CURRENCY, fractionSize: 2},
        COST_PER_VISIT: {name: 'Avg. Cost per Visit', value: 'avg_cost_per_visit', type: TYPE_CURRENCY, fractionSize: 2},
        COST_PER_NON_BOUNCED_VISIT: {name: 'Avg. Cost per Non-Bounced Visit', value: 'avg_cost_per_non_bounced_visit', type: TYPE_CURRENCY, fractionSize: 2},
        COST_PER_NEW_VISITOR: {name: 'Avg. Cost for New Visitor', value: 'avg_cost_for_new_visitor', type: TYPE_CURRENCY, fractionSize: 2},
    }; /* eslint-enable max-len */

    var TRAFFIC_ACQUISITION = [
        METRICS.IMPRESSIONS,
        METRICS.CLICKS,
        METRICS.CTR,
        METRICS.CPC,
        METRICS.CPM,
    ];

    var COST_METRICS = [
        METRICS.MEDIA_COST,
        METRICS.E_MEDIA_COST,
        METRICS.DATA_COST,
        METRICS.E_DATA_COST,
        METRICS.LICENSE_FEE,
        METRICS.BILLING_COST,
    ];

    var POST_CLICK_METRICS = [
        METRICS.VISITS,
        METRICS.UNIQUE_USERS,
        METRICS.NEW_USERS,
        METRICS.RETURNING_USERS,
        METRICS.PERCENT_NEW_USERS,
        METRICS.CLICK_DISCREPANCY,
        METRICS.PAGEVIEWS,
        METRICS.PV_PER_VISIT,
        METRICS.BOUNCED_VISITS,
        METRICS.NON_BOUNCED_VISITS,
        METRICS.BOUNCE_RATE,
        METRICS.TOTAL_SECONDS,
        METRICS.AVG_TOS
    ];

    var GOAL_METRICS = [
        METRICS.COST_PER_VISIT,
        METRICS.COST_PER_NEW_VISITOR,
        METRICS.COST_PER_PAGEVIEW,
        METRICS.COST_PER_NON_BOUNCED_VISIT,
        METRICS.COST_PER_MINUTE
    ];

    var AUDIENCE_METRICS = [].concat(POST_CLICK_METRICS, GOAL_METRICS);

    ////////////////////////////////////////////////////////////////////////////////////
    // Service functions
    //
    function getChartMetrics () {
        var categories = [];
        categories.push({name: COSTS_CATEGORY_NAME, metrics: createMetrics(COST_METRICS)});
        categories.push({name: TRAFFIC_CATEGORY_NAME, metrics: createMetrics(TRAFFIC_ACQUISITION)});
        categories.push({name: AUDIENCE_CATEGORY_NAME, metrics: createMetrics(AUDIENCE_METRICS)});

        return categories;
    }

    function createMetrics (metricDefinitions) {
        return metricDefinitions.map(function (metricDefinition) {
            var metric = angular.copy(metricDefinition);
            metric.internal = metric.permission ? zemPermissions.isPermissionInternal(metric.permission) : false;
            metric.isShown = metric.permission ? zemPermissions.hasPermission(metric.permission) : true;
            return metric;
        }).filter(function (metric) { return metric.isShown; });
    }

    function insertDynamicMetrics (categories, pixels, conversionGoals) {

        if (!findCategoryByName(categories, PIXELS_CATEGORY_NAME)) {
            insertPixelCategory(categories, pixels);
        }

        if (!findCategoryByName(categories, CONVERSIONS_CATEGORY_NAME)) {
            insertConversionCategory(categories, conversionGoals);
        }
    }

    function insertPixelCategory (categories, pixels) {
        if (!pixels || pixels.length === 0) return;
        var pixelSubcategories = [];
        angular.forEach(pixels, function (pixel) {
            var pixelMetrics = [];
            var pixelGoalMetrics = [];
            angular.forEach(options.conversionWindows, function (conversionWindow) {
                var metricValue = pixel.prefix + '_' + conversionWindow.value;
                pixelMetrics.push({
                    value: metricValue,
                    shortName: conversionWindow.value / 24,
                    name: pixel.name + ' ' + conversionWindow.name
                });

                pixelGoalMetrics.push({
                    value: 'avg_cost_per_' + metricValue,
                    shortName: conversionWindow.value / 24,
                    name: 'CPA(' + pixel.name + ' ' + conversionWindow.name + ')'
                });
            });

            pixelSubcategories.push({
                name: pixel.name,
                metrics: pixelMetrics,
            });

            pixelSubcategories.push({
                name: 'CPA (' + pixel.name + ')',
                metrics: pixelGoalMetrics,
            });
        });
        categories.push({
            name: PIXELS_CATEGORY_NAME,
            description: 'Choose conversion window in days.',
            metrics: [],
            subcategories: pixelSubcategories
        });
    }

    function insertConversionCategory (categories, conversionGoals) {
        if (!conversionGoals || conversionGoals.length === 0) return;
        var conversionMetrics = [];
        var conversionGoalMetrics = [];
        angular.forEach(conversionGoals, function (goal) {
            conversionMetrics.push({
                value: goal.id,
                name: goal.name,
            });

            conversionGoalMetrics.push({
                value: 'avg_cost_per_' + goal.id,
                name: 'CPA (' + goal.name + ')',
                type: TYPE_CURRENCY,
                fractionSize: 2
            });
        });
        categories.push({
            name: CONVERSIONS_CATEGORY_NAME,
            metrics: [].concat(conversionMetrics, conversionGoalMetrics)
        });
    }

    function findCategoryByName (categories, name) {
        return categories.filter(function (c) { return c.name === name; })[0];
    }

    function findMetricByValue (categories, metricValue) {
        for (var i = 0; i < categories.length; ++i) {
            var category = categories[i];
            for (var j = 0; j < category.metrics.length; ++j) {
                var metric = category.metrics[j];
                if (metric.value === metricValue) {
                    return metric;
                }
            }
        }

        return null;
    }

    return {
        METRICS: METRICS,
        getChartMetrics: getChartMetrics,
        insertDynamicMetrics: insertDynamicMetrics,
        findMetricByValue: findMetricByValue,
        findCategoryByName: findCategoryByName
    };
});
