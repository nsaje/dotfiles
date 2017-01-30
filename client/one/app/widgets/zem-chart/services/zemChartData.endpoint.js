angular.module('one.widgets').service('zemChartEndpoint', function ($q, $http, zemUtils, zemPermissions, zemChartMetricsService) { // eslint-disable-line max-len

    function EndpointService (metaData) {
        this.getMetaData = getMetaData;
        this.getData = getData;

        function getMetaData () {
            return metaData;
        }

        function getData (config) {
            var deferred = zemUtils.createAbortableDefer();
            config = {
                params: convertToApi(config),
                timeout: deferred.abortPromise,
            };

            $http.get(metaData.url, config).
                then(function (response) {
                    var chartData, conversionGoals, pixels;
                    if (response.data.data) {
                        var data = response.data.data;
                        if (data.chart_data) {
                            chartData = {
                                groups: data.chart_data.map(function (group) {
                                    return convertFromApi(group);
                                }),
                                campaignGoals: data.campaign_goals,
                                goalFields: data.goal_fields,
                            };
                        }
                        zemChartMetricsService.insertDynamicMetrics(
                            metaData.metrics, data.pixels, data.conversion_goals);
                    }
                    deferred.resolve({
                        chartData: chartData,
                        conversionGoals: conversionGoals,
                        pixels: pixels,
                    });
                }).catch(function (response) {
                    if (response.status === -1) { // request was aborted, do nothing
                        return;
                    }
                    deferred.reject(response.data);
                });

            return deferred.promise;
        }

        function convertFromApi (group) {
            return {
                id: group.id,
                name: group.name,
                seriesData: group.series_data
            };
        }

        function convertToApi (config) {
            var converted = {};

            converted.metrics = config.metrics;
            converted.start_date = config.dateRange.startDate.format();
            converted.end_date = config.dateRange.endDate.format();

            converted.totals = config.totals;
            converted.select_all = config.selection.selectAll ? config.selection.selectAll : undefined;
            converted.select_batch = config.selection.batchId;
            converted.selected_ids = config.selection.selectedIds ? config.selection.selectedIds : undefined;
            converted.not_selected_ids = config.selection.unselectedIds ? config.selection.unselectedIds : undefined;

            converted.filtered_sources = config.filteredSources ? config.filteredSources.join(',') : undefined;
            converted.filtered_agencies = config.filteredAgencies;
            converted.filtered_account_types = config.filteredAccountTypes;
            converted.show_blacklisted_publishers = config.filteredPublisherStatus;

            return converted;
        }
    }

    var breakdownUrlMap = {};
    breakdownUrlMap[constants.breakdown.ACCOUNT] = 'accounts';
    breakdownUrlMap[constants.breakdown.CAMPAIGN] = 'campaigns';
    breakdownUrlMap[constants.breakdown.AD_GROUP] = 'ad_groups';
    breakdownUrlMap[constants.breakdown.CONTENT_AD] = 'contentads';
    breakdownUrlMap[constants.breakdown.MEDIA_SOURCE] = 'sources';
    breakdownUrlMap[constants.breakdown.PUBLISHER] = 'publishers';
    function getUrl (level, id, breakdown) {
        // /api/${level}/${id}/${breakdown}/daily_stats
        return '/api/' + level + (id ? ('/' + id) : '') + '/' + breakdownUrlMap[breakdown] + '/daily_stats/';
    }

    function createEndpoint (metaData) {
        return new EndpointService(metaData);

    }

    function createMetaData (level, id, breakdown) {
        return {
            id: id,
            level: level,
            breakdown: breakdown,
            url: getUrl(level, id, breakdown),
            metrics: zemChartMetricsService.getChartMetrics(level),
        };
    }


    return {
        createEndpoint: createEndpoint,
        createMetaData: createMetaData,
    };
});
