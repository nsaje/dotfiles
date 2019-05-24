angular
    .module('one.widgets')
    .service('zemReportService', function(
        $q,
        zemReportEndpoint,
        zemPermissions,
        zemDataFilterService,
        zemUtils
    ) {
        // eslint-disable-line max-len

        // Public API
        this.startReport = startReport;
        this.getReport = getReport;
        this.scheduleReport = scheduleReport;

        function getReport(id) {
            var deferred = $q.defer();

            zemReportEndpoint
                .getReport(id)
                .then(function(response) {
                    deferred.resolve(response.data);
                })
                .catch(function(response) {
                    deferred.reject(response.data);
                });

            return deferred.promise;
        }

        function scheduleReport(
            gridApi,
            queryConfig,
            recipients,
            name,
            frequency,
            timePeriod,
            dayOfWeek
        ) {
            var deferred = $q.defer();

            var config = {
                name: name,
                query: getQueryConfig(gridApi, queryConfig, recipients),
                frequency: frequency,
                timePeriod: timePeriod,
                dayOfWeek: dayOfWeek,
            };

            zemReportEndpoint
                .scheduleReport(zemUtils.convertToUnderscore(config))
                .then(function(response) {
                    deferred.resolve(response.data);
                })
                .catch(function(response) {
                    deferred.reject(response.data);
                });

            return deferred.promise;
        }

        function startReport(gridApi, queryConfig, recipients) {
            var deferred = $q.defer();

            var config = getQueryConfig(gridApi, queryConfig, recipients);

            zemReportEndpoint
                .startReport(config)
                .then(function(response) {
                    deferred.resolve(response.data);
                })
                .catch(function(response) {
                    deferred.reject(response.data);
                });

            return deferred.promise;
        }

        function getQueryConfig(gridApi, queryConfig, recipients) {
            var dateRange = zemDataFilterService.getDateRange();

            var config = {
                fields: queryConfig.selectedFields.map(function(field) {
                    return {field: field};
                }),
                filters: [
                    {
                        field: 'Date',
                        operator: 'between',
                        from: dateRange.startDate.format('YYYY-MM-DD'),
                        to: dateRange.endDate.format('YYYY-MM-DD'),
                    },
                ],
                options: {
                    recipients: recipients,
                    showArchived: zemDataFilterService.getShowArchived(),
                    includeTotals: queryConfig.includeTotals || false,
                    includeItemsWithNoSpend:
                        queryConfig.includeItemsWithNoSpend || false,
                    includeEntityTags: queryConfig.includeEntityTags || false,
                    allAccountsInLocalCurrency:
                        queryConfig.allAccountsInLocalCurrency || false,
                    csvSeparator: queryConfig.csvSeparator,
                    csvDecimalSeparator: queryConfig.csvDecimalSeparator,
                    showStatusDate: true,
                    order: getOrder(gridApi),
                },
            };

            var levelFilter = getLevelFilter(gridApi);
            if (levelFilter) {
                config.filters.push(levelFilter);
            }

            var filteredSources = zemDataFilterService.getFilteredSources();
            if (filteredSources) {
                config.filters.push({
                    field: 'Media Source',
                    operator: 'IN',
                    values: filteredSources,
                });
            }

            var filteredAccountTypes = zemDataFilterService.getFilteredAccountTypes();
            if (filteredAccountTypes) {
                config.filters.push({
                    field: 'Account Type',
                    operator: 'IN',
                    values: filteredAccountTypes,
                });
            }

            var filteredAgencies = zemDataFilterService.getFilteredAgencies();
            if (filteredAgencies) {
                config.filters.push({
                    field: 'Agency',
                    operator: 'IN',
                    values: filteredAgencies,
                });
            }

            var filteredPublisherStatus = zemDataFilterService.getFilteredPublisherStatus();
            if (filteredPublisherStatus) {
                config.options.showBlacklistedPublishers = filteredPublisherStatus;
            }

            return config;
        }

        function getOrder(gridApi) {
            var prefix = '',
                orderFieldKey = gridApi.getOrder();

            if (orderFieldKey[0] === '-') {
                prefix = '-';
                orderFieldKey = orderFieldKey.slice(1);
            } else if (orderFieldKey[0] === '+') {
                prefix = '';
                orderFieldKey = orderFieldKey.slice(1);
            }

            var orderField,
                columns = gridApi.getColumns();
            for (var i = 0; i < columns.length; i++) {
                if (
                    columns[i].orderField === orderFieldKey ||
                    columns[i].field === orderFieldKey
                ) {
                    orderField = columns[i].data.name;
                    break;
                }
            }

            return prefix + orderField;
        }

        function getLevelFilter(gridApi) {
            var metaData = gridApi.getMetaData();
            if (metaData.level === constants.level.AD_GROUPS) {
                return {
                    field: 'Ad Group Id',
                    operator: '=',
                    value: metaData.id,
                };
            } else if (metaData.level === constants.level.CAMPAIGNS) {
                return {
                    field: 'Campaign Id',
                    operator: '=',
                    value: metaData.id,
                };
            } else if (metaData.level === constants.level.ACCOUNTS) {
                return {
                    field: 'Account Id',
                    operator: '=',
                    value: metaData.id,
                };
            }
        }
    });
