angular.module('one.widgets').service('zemReportEndpoint', function ($http) {
    this.startReport = startReport;
    this.getReport = getReport;

    function startReport (config) {
        var url = '/rest/v1/reports/';
        return $http.post(url, config);
    }

    function getReport (id) {
        var url = '/rest/v1/reports/' + id;
        return $http.get(url);
    }
});
