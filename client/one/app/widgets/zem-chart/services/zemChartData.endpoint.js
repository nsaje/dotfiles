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
                        if (data.conversion_goals) {
                            conversionGoals = data.conversion_goals;
                            zemChartMetricsService.insertConversionsGoalChartOptions(metaData.metrics, conversionGoals);
                        }
                        if (data.pixels) {
                            pixels = data.pixels;
                            zemChartMetricsService.insertPixelChartOptions(metaData.metrics, pixels);
                        }
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

    function getChartMetrics (level) {
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
        var chartMetricOptions = entityChartMetrics;

        if (zemPermissions.hasPermission('zemauth.aggregate_postclick_acquisition')) {
            chartMetricOptions = zemChartMetricsService.concatAcquisitionChartOptions(
                chartMetricOptions,
                zemPermissions.isPermissionInternal('zemauth.aggregate_postclick_acquisition')
            );
        }

        if (zemPermissions.hasPermission('zemauth.aggregate_postclick_engagement')) {
            chartMetricOptions = zemChartMetricsService.concatEngagementChartOptions(
                chartMetricOptions,
                zemPermissions.isPermissionInternal('zemauth.aggregate_postclick_engagement')
            );
        }

        if (zemPermissions.hasPermission('zemauth.can_view_platform_cost_breakdown')) {
            chartMetricOptions = zemChartMetricsService.concatChartOptions(
                chartMetricOptions,
                options.platformCostChartMetrics,
                zemPermissions.isPermissionInternal('zemauth.can_view_platform_cost_breakdown')
            );
        }

        chartMetricOptions = zemChartMetricsService.concatChartOptions(
            chartMetricOptions,
            options.billingCostChartMetrics,
            false
        );

        if (zemPermissions.hasPermission('zemauth.can_view_actual_costs')) {
            chartMetricOptions = zemChartMetricsService.concatChartOptions(
                chartMetricOptions,
                options.actualCostChartMetrics,
                zemPermissions.isPermissionInternal('zemauth.can_view_actual_costs')
            );
        }

        chartMetricOptions = zemChartMetricsService.concatChartOptions(
            chartMetricOptions,
            options.conversionChartMetrics
        );

        chartMetricOptions = zemChartMetricsService.concatChartOptions(
            chartMetricOptions,
            options.goalChartMetrics
        );

        return chartMetricOptions;
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
            metrics: getChartMetrics(level),
        };
    }


    return {
        createEndpoint: createEndpoint,
        createMetaData: createMetaData,
    };
});
