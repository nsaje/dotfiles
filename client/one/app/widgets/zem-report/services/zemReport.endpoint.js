angular.module('one.widgets').service('zemReportEndpoint', ['$http', function ($http) {
    this.startReport = startReport;

    // TODO does it make sense to have a separate service when endpoint is so small

    function startReport (config) {
        var url = '/rest/v1/reports/';
        return $http.post(url, config);
    }
}]);