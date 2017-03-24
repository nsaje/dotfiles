angular.module('one.widgets').service('zemReportService', function ($q, zemReportEndpoint, zemPermissions, zemDataFilterService) {  // eslint-disable-line max-len

    // Public API
    this.startReport = startReport;

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
            fields: getFields(selectedFields, includeConfig),
            filters: [
                {
                    field: 'Date',
                    operator: 'between',
                    from: dateRange.startDate.format('YYYY-MM-DD'),
                    to: dateRange.endDate.format('YYYY-MM-DD'),
                },
            ],
            options: {
                emailReport: true,
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
                deferred.resolve(response);
            })
            .catch(function (response) {
                deferred.reject(response);
            });

        return deferred.promise;
    }

    function getFields (selectedFieldNames, includeConfig) {
        var fieldsWithIds = ['Content Ad', 'Ad Group', 'Campaign', 'Account', 'Agency'];
        var includeIds = includeConfig.includeIds || selectedFieldNames.indexOf('Id') >= 0;
        var fields = [];
        for (var i = 0; i < selectedFieldNames.length; i++) {
            if (selectedFieldNames[i] === 'Id') continue;
            if (includeIds && fieldsWithIds.indexOf(selectedFieldNames[i]) >= 0) {
                fields.push({
                    field: selectedFieldNames[i] + ' Id',
                });
            }
            fields.push({
                field: selectedFieldNames[i],
            });
        }
        return fields;
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
