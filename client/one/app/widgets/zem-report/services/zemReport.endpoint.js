angular.module('one.widgets').service('zemReportEndpoint', function ($http) {
    this.startReport = startReport;

    function startReport (config) {
        var url = '/rest/v1/reports/';
        return $http.post(url, config);
    }
});