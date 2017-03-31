angular.module('one.widgets').service('zemReportService', function ($q, zemReportEndpoint, zemPermissions, zemDataFilterService) {  // eslint-disable-line max-len

    // Public API
    this.startReport = startReport;
    this.getReport = getReport;

    function getReport (id) {
        var deferred = $q.defer();

        zemReportEndpoint
            .getReport(id)
            .then(function (response) {
                deferred.resolve(response.data);
            })
            .catch(function (response) {
                deferred.reject(response.data);
            });

        return deferred.promise;
    }

    function startReport (gridApi, selectedFields, includeConfig) {
        var deferred = $q.defer();

        var dateRange = zemDataFilterService.getDateRange();

        var showArchived = zemDataFilterService.getShowArchived();
        var filteredSources = zemDataFilterService.getFilteredSources();
        var filteredPublisherStatus = zemDataFilterService.getFilteredPublisherStatus();
        var filteredAccountTypes = zemDataFilterService.getFilteredAccountTypes();
        var filteredAgencies = zemDataFilterService.getFilteredAgencies();
        var levelFilter = getLevelFilter(gridApi);

        var config = {
            fields: selectedFields.map(function (field) { return {'field': field}; }),
            filters: [
                {
                    field: 'Date',
                    operator: 'between',
                    from: dateRange.startDate.format('YYYY-MM-DD'),
                    to: dateRange.endDate.format('YYYY-MM-DD'),
                },
            ],
            options: {
                emailReport: includeConfig.sendReport,
                recipients: includeConfig.recipients,
                showArchived: showArchived,
                includeTotals: includeConfig.includeTotals || false,
                includeItemsWithNoSpend: includeConfig.includeItemsWithNoSpend || false,
                showStatusDate: true,
                order: getOrder(gridApi),
            },
        };

        if (levelFilter) {
            config.filters.push(levelFilter);
        }

        if (filteredSources) {
            config.filters.push({
                field: 'Media Source',
                operator: 'IN',
                values: filteredSources,
            });
        }

        if (filteredAccountTypes) {
            config.filters.push({
                field: 'Account Type',
                operator: 'IN',
                values: filteredAccountTypes,
            });
        }

        if (filteredAgencies) {
            config.filters.push({
                field: 'Agency',
                operator: 'IN',
                values: filteredAgencies,
            });
        }

        if (filteredPublisherStatus) {
            config.options.showBlacklistedPublishers = filteredPublisherStatus;
        }

        zemReportEndpoint
            .startReport(config)
            .then(function (response) {
                deferred.resolve(response.data);
            })
            .catch(function (response) {
                deferred.reject(response.data);
            });

        return deferred.promise;
    }

    function getOrder (gridApi) {
        var prefix = '', orderFieldKey = gridApi.getOrder();

        if (orderFieldKey[0] === '-') {
            prefix = '-';
            orderFieldKey = orderFieldKey.slice(1);
        } else if (orderFieldKey[0] === '+') {
            prefix = '';
            orderFieldKey = orderFieldKey.slice(1);
        }

        var orderField, columns = gridApi.getColumns();
        for (var i = 0; i < columns.length; i++) {
            if (columns[i].orderField === orderFieldKey || columns[i].field === orderFieldKey) {
                orderField = columns[i].data.name;
                break;
            }
        }

        return prefix + orderField;
    }

    function getLevelFilter (gridApi) {
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
