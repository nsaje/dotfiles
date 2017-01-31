angular.module('one.widgets').service('zemChartDataService', function ($q, zemDataFilterService, zemChartEndpoint, zemChartParser) { // eslint-disable-line max-len

    function ChartDataService (chart, endpoint) {
        var getDataPromise = undefined;

        var metrics = [constants.chartMetric.COST, constants.chartMetric.IMPRESSIONS];

        this.initialize = initialize;
        this.getData = getData;
        this.getMetaData = getMetaData;

        this.setMetrics = setMetrics;
        this.getMetrics = getMetrics;

        var selection = {};
        this.setSelection = setSelection;

        function initialize () {
            applyMetaData(getMetaData());
        }

        function getMetaData () {
            return endpoint.getMetaData();
        }

        function getData () {
            chart.isLoading = true;
            if (getDataPromise) {
                getDataPromise.abort();
            }

            var config = createConfig();

            var deferred = $q.defer();
            getDataPromise = endpoint.getData(config);
            getDataPromise.then(function (data) {
                applyMetaData(endpoint.getMetaData());
                applyData(data.chartData);
                deferred.resolve();
            }, function (err) {
                deferred.reject(err);
            }).finally(function () {
                chart.isLoading = false;
            });
            return deferred.promise;
        }

        function createConfig () {
            return {
                metrics: metrics,
                dateRange: zemDataFilterService.getDateRange(),
                filteredSources: zemDataFilterService.getFilteredSources(),
                filteredAgencies: zemDataFilterService.getFilteredAgencies(),
                filteredAccountTypes: zemDataFilterService.getFilteredAccountTypes(),
                filteredPublisherStatus: zemDataFilterService.getFilteredPublisherStatus(),
                selection: selection,
                totals: selection.totals,
            };
        }

        function applyMetaData (metaData) {
            zemChartParser.parseMetaData(chart, metaData);
        }

        function applyData (chartData) {
            chart.clearData();
            var data = chartData && chartData.groups;

            // Undefined means that no data has been assigned yet but will be.
            if (data === undefined) {
                chart.hasData = true;
                return;
            }

            zemChartParser.parseData(chart, data, metrics, zemDataFilterService.getDateRange());
        }

        function setMetrics (_metrics, fetch) {
            metrics = _metrics;
            if (fetch) getData();
        }

        function getMetrics () {
            return metrics;
        }

        function setSelection (_selection, fetch) {
            selection = _selection;
            if (fetch) getData();
        }
    }

    return {
        createInstance: function (chart, endpoint) {
            return new ChartDataService(chart, endpoint);
        },
    };
});
