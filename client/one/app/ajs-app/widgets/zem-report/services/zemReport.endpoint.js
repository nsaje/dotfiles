angular.module('one.widgets').service('zemReportEndpoint', function($http) {
    this.startReport = startReport;
    this.getReport = getReport;
    this.scheduleReport = scheduleReport;

    function startReport(config) {
        var url = '/rest/v1/reports/';
        return $http.post(url, config);
    }

    function getReport(id) {
        var url = '/rest/v1/reports/' + id;
        return $http.get(url);
    }

    function scheduleReport(config) {
        var url = '/api/scheduled_reports/';
        return $http.put(url, config);
    }
});
