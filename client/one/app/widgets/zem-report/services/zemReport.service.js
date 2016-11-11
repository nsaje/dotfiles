angular.module('one.widgets').service('zemReportService', function ($q, zemReportEndpoint, zemDataFilterService) {

    // Public API
    this.startReport = startReport;

    function startReport (gridApi, includeConfig) {  // eslint-disable-line no-unused-vars
        var deferred = $q.defer();

        var dateRange = zemDataFilterService.getDateRange();

        var config = {
            fields: [
                {field: 'Domain Id'},
                {field: 'Domain'},
                {field: 'Media Source'},
                {field: 'Clicks'},
                {field: 'Impressions'},
            ],
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
                }
            ],
            options: {
                emailReport: true,
            },

        };

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
});