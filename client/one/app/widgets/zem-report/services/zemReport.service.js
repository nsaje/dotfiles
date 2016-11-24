angular.module('one.widgets').service('zemReportService', function ($q, zemReportEndpoint, zemDataFilterService) {

    // Public API
    this.startReport = startReport;

    function startReport (gridApi, includeConfig) {  // eslint-disable-line no-unused-vars
        var deferred = $q.defer();

        var dateRange = zemDataFilterService.getDateRange();

        var config = {
            fields: getSelectedFields(gridApi),
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

    function getSelectedFields (gridApi) {
        var fields = [], columns = gridApi.getColumns();

        var breakdown = gridApi.getBreakdown();
        for (var i = 0; i < breakdown.length; i++) {
            fields.push({
                field: breakdown[i].report_query,
            });
        }

        for (i = 0; i < columns.length; i++) {
            if (columns[i].visible && columns[i].data.name) {
                fields.push({
                    field: columns[i].data.name,
                });
            }
        }

        return fields;
    }
});