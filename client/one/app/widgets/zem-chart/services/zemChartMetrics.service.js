/* globals options,constants,angular */
'use strict';

angular.module('one.widgets').factory('zemChartMetricsService', function (zemPermissions) {

    function createMetrics (metricDefinitions, permission) {
        var isShown = permission ? zemPermissions.hasPermission(permission) : true;
        if (!isShown) return [];

        var isInternal = permission ? zemPermissions.isPermissionInternal(permission) : false;
        return metricDefinitions.map(function (metric) {
            return {
                name: metric.name,
                value: metric.value,
                internal: isInternal
            };
        });
    }

    function getEntityChartMetrics (level) {

        var entityChartMetrics;
        switch (level) {
        case constants.level.ALL_ACCOUNTS:
            entityChartMetrics = options.allAccountsChartMetrics;
            break;
        case constants.level.ACCOUNTS:
            entityChartMetrics = options.accountChartMetrics;
            break;
        case constants.level.CAMPAIGNS:
            entityChartMetrics = options.campaignChartMetrics;
            break;
        case constants.level.AD_GROUPS:
            entityChartMetrics = options.adGroupChartMetrics;
            break;
        }
        return entityChartMetrics;
    }

    function getChartMetrics (level) {
        var categories = [];

        // Costs
        var costMetrics = [].concat(
            createMetrics(options.platformCostChartMetrics, 'zemauth.can_view_platform_cost_breakdown'),
            createMetrics(options.billingCostChartMetrics),
            createMetrics(options.actualCostChartMetrics, 'zemauth.can_view_actual_costs')
        );
        categories.push({name: 'Costs', metrics: costMetrics});

        // Traffic Acquisition
        var entityMetrics = createMetrics(getEntityChartMetrics(level));
        categories.push({name: 'Traffic Acquisition', metrics: entityMetrics});

        // Audience Metrics
        var audienceMetrics = [].concat(
            createMetrics(options.adGroupEngagementChartPostClickMetrics, 'zemauth.aggregate_postclick_engagement'),
            createMetrics(options.adGroupAcquisitionChartPostClickMetrics, 'zemauth.aggregate_postclick_acquisition'),
            createMetrics(options.goalChartMetrics)
        );
        categories.push({name: 'Audience Metrics', metrics: audienceMetrics});

        // Conversion & CPAs
        //categories.push({name: 'Conversions & CPAs', metrics: createMetrics(options.conversionChartMetrics)});

        return categories;

    }

    var CONVERSIONS_CATEGORY_NAME = 'Google & Adobe Analytics Goals';
    var PIXELS_CATEGORY_NAME = 'Conversions & CPAs';

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
        getChartMetrics: getChartMetrics,
        insertDynamicMetrics: insertDynamicMetrics,
        findMetricByValue: findMetricByValue,
        findCategoryByName: findCategoryByName
    };
});
