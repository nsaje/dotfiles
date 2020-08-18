angular
    .module('one.widgets')
    .service('zemChartService', function(
        zemChartDataService,
        zemChartEndpoint
    ) {
        // eslint-disable-line max-len

        this.createDataService = createDataService;

        function createDataService(chart, level, breakdown, id) {
            var metaData = zemChartEndpoint.createMetaData(
                level,
                id,
                breakdown
            );
            var endpoint = zemChartEndpoint.createEndpoint(metaData);
            return zemChartDataService.createInstance(chart, endpoint);
        }
    });
