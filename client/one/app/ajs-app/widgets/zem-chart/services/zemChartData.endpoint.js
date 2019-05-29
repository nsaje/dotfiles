angular
    .module('one.widgets')
    .service('zemChartEndpoint', function(
        $q,
        $http,
        zemUtils,
        zemPermissions,
        zemChartMetricsService,
        zemChartMetaDataService
    ) {
        // eslint-disable-line max-len

        function EndpointService(metaData) {
            this.getMetaData = getMetaData;
            this.getData = getData;

            function getMetaData() {
                return metaData;
            }

            function getData(config) {
                var deferred = zemUtils.createAbortableDefer();
                config = {
                    params: convertToApi(config),
                    timeout: deferred.abortPromise,
                };

                $http
                    .get(metaData.url, config)
                    .then(function(response) {
                        var chartData, conversionGoals, pixels;
                        if (response.data.data) {
                            var data = response.data.data;
                            if (data.chart_data) {
                                chartData = {
                                    groups: data.chart_data.map(function(
                                        group
                                    ) {
                                        return convertFromApi(group);
                                    }),
                                    campaignGoals: data.campaign_goals,
                                    goalFields: data.goal_fields,
                                };

                                if (
                                    chartData.groups.length > 1 &&
                                    chartData.groups[0].id === 'totals' &&
                                    !config.params.totals
                                ) {
                                    // WORKAROUND: if 'totals' stats wat not requested and
                                    // there is more data available remove it from the result
                                    chartData.groups.shift();
                                }
                            }
                            metaData.setCurrency(data.currency);
                            metaData.insertDynamicMetrics(
                                metaData.metrics,
                                data.pixels,
                                data.conversion_goals
                            );
                        }
                        deferred.resolve({
                            chartData: chartData,
                            conversionGoals: conversionGoals,
                            pixels: pixels,
                        });
                    })
                    .catch(function(response) {
                        if (response.status === -1) {
                            // request was aborted, do nothing
                            return;
                        }
                        deferred.reject(response.data);
                    });

                return deferred.promise;
            }

            function convertFromApi(group) {
                return {
                    id: group.id,
                    name: group.name,
                    seriesData: group.series_data,
                };
            }

            function convertToApi(config) {
                var converted = {};

                converted.metrics = config.metrics;
                converted.start_date = config.dateRange.startDate.format(
                    'YYYY-MM-DD'
                );
                converted.end_date = config.dateRange.endDate.format(
                    'YYYY-MM-DD'
                );

                converted.totals = config.totals;
                converted.select_all = config.selection.selectAll
                    ? config.selection.selectAll
                    : undefined;
                converted.select_batch = config.selection.batchId;
                converted.selected_ids = config.selection.selectedIds
                    ? config.selection.selectedIds
                    : undefined;
                converted.not_selected_ids = config.selection.unselectedIds
                    ? config.selection.unselectedIds
                    : undefined;

                converted.filtered_sources = config.filteredSources
                    ? config.filteredSources.join(',')
                    : undefined;
                converted.filtered_agencies = config.filteredAgencies
                    ? config.filteredAgencies.join(',')
                    : undefined;
                converted.filtered_account_types = config.filteredAccountTypes
                    ? config.filteredAccountTypes.join(',')
                    : undefined;
                converted.show_blacklisted_publishers =
                    config.filteredPublisherStatus;
                converted.show_archived = config.showArchived;

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
        breakdownUrlMap[constants.breakdown.COUNTRY] = 'country';
        breakdownUrlMap[constants.breakdown.STATE] = 'region';
        breakdownUrlMap[constants.breakdown.DMA] = 'dma';
        breakdownUrlMap[constants.breakdown.DEVICE] = 'device_type';
        breakdownUrlMap[constants.breakdown.PLACEMENT] = 'placement_medium';
        breakdownUrlMap[constants.breakdown.OPERATING_SYSTEM] = 'device_os';

        function getUrl(level, id, breakdown) {
            // /api/${level}/${id}/${breakdown}/daily_stats
            return (
                '/api/' +
                level +
                (id ? '/' + id : '') +
                '/' +
                breakdownUrlMap[breakdown] +
                '/daily_stats/'
            );
        }

        function createEndpoint(metaData) {
            return new EndpointService(metaData);
        }

        function createMetaData(level, id, breakdown) {
            var url = getUrl(level, id, breakdown);
            return zemChartMetaDataService.createInstance(
                level,
                id,
                breakdown,
                url
            );
        }

        return {
            createEndpoint: createEndpoint,
            createMetaData: createMetaData,
        };
    });
