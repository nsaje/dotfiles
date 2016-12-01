angular.module('one.widgets').service('zemReportService', function ($q, zemReportEndpoint, zemPermissions, zemFilterService, zemDataFilterService) {  // eslint-disable-line max-len

    // Public API
    this.startReport = startReport;

    function startReport (gridApi, selectedFields, includeConfig) {  // eslint-disable-line no-unused-vars
        var deferred = $q.defer();

        var dateRange = zemDataFilterService.getDateRange();

        // TODO: old filter is used, migrate to the new one when available
        var showArchived = zemFilterService.getShowArchived();
        var filteredSources = zemFilterService.getFilteredSources();
        var filteredPublisherStatus = zemFilterService.getBlacklistedPublishers();

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
});