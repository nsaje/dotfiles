angular.module('one.widgets').factory('zemChartMetaDataService', function (zemChartMetricsService, zemPubSubService) { // eslint-disable-line max-len

    function MetaData (level, id, breakdown, url) {
        var METRICS_UPDATED = 'zem-chart-metrics-updated';
        var pubsub = zemPubSubService.createInstance();

        this.id = id;
        this.level = level;
        this.breakdown = breakdown;
        this.url = url;
        this.metrics = zemChartMetricsService.getChartMetrics(level);

        this.insertDynamicMetrics = insertDynamicMetrics;

        // Listeners - pubsub rewiring
        this.onMetricsUpdated = onMetricsUpdated;

        function onMetricsUpdated (callback) {
            pubsub.register(METRICS_UPDATED, callback);
        }

        function insertDynamicMetrics (categories, pixels, conversionGoals) {
            zemChartMetricsService.insertDynamicMetrics(categories, pixels, conversionGoals);
            pubsub.notify(METRICS_UPDATED);
        }
    }

    return {
        createInstance: function (level, id, breakdown, url) {
            return new MetaData(level, id, breakdown, url);
        },
    };
});
