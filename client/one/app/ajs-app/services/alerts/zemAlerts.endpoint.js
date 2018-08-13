angular.module('one.services').service('zemAlertsEndpoint', function($http) {
    this.getAlerts = getAlerts;

    function getAlerts(level, entityId) {
        var url;
        if (level === constants.level.ALL_ACCOUNTS) {
            url = '/api/' + level + '/alerts/';
        } else {
            url = '/api/' + level + '/' + entityId + '/alerts/';
        }
        return $http.get(url);
    }
});
