angular.module('one.widgets').service('zemReportService', function ($q, zemReportEndpoint, zemPermissions, zemDataFilterService) {  // eslint-disable-line max-len

    // Public API
    this.startReport = startReport;

    function startReport (gridApi, selectedFields, includeConfig) {
        var deferred = $q.defer();

        var dateRange = zemDataFilterService.getDateRange();

        var showArchived = zemDataFilterService.getShowArchived();
        var filteredSources = zemDataFilterService.getFilteredSources();
        var filteredPublisherStatus = zemDataFilterService.getFilteredPublisherStatus();

        var config = {
            fields: getFields(selectedFields),
            filters: [
                {
                    field: 'Date',
                    operator: 'between',
                    from: dateRange.startDate.format('YYYY-MM-DD'),
                    to: dateRange.endDate.format('YYYY-MM-DD'),
                },
                {
                    field: 'Ad Group Id',
                    operator: '=',
                    value: gridApi.getMetaData().id,
                },
            ],
            options: {
                emailReport: true,
                recipients: includeConfig.recipients,
                showArchived: showArchived,
                includeTotals: includeConfig.includeTotals || false,
                showStatusDate: true,
                order: getOrder(gridApi),
            },
        };

        if (filteredSources) {
            config.filters.push({
                field: 'Media Source',
                operator: 'IN',
                values: filteredSources,
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

    function getFields (selectedFieldNames) {
        var fields = [];
        for (var i = 0; i < selectedFieldNames.length; i++) {
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
});