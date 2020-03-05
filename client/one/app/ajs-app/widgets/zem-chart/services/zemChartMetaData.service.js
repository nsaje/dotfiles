var clone = require('clone');

angular
    .module('one.widgets')
    .factory('zemChartMetaDataService', function(zemChartMetricsService) {
        // eslint-disable-line max-len

        function MetaData(level, id, breakdown, url) {
            this.id = id;
            this.level = level;
            this.breakdown = breakdown;
            this.url = url;
            this.metrics = zemChartMetricsService.getChartMetrics(level);

            this.insertDynamicMetrics = insertDynamicMetrics;
            this.setCurrency = setCurrency;

            function insertDynamicMetrics(pixels, conversionGoals) {
                var clonedMetrics = clone(this.metrics);
                zemChartMetricsService.insertDynamicMetrics(
                    clonedMetrics,
                    pixels,
                    conversionGoals
                );
                this.metrics = clonedMetrics;
            }

            function setCurrency(currency) {
                this.currency = currency;
            }
        }

        return {
            createInstance: function(level, id, breakdown, url) {
                return new MetaData(level, id, breakdown, url);
            },
        };
    });
