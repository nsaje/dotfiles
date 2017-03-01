angular.module('one.widgets').service('zemPublisherGroupsEndpoint', function ($q, $http, $window) {
    this.get = get;
    this.download = download;

    function get (accountId) {
        var url = '/api/accounts/' + accountId + '/publisher_groups/';
        var config = {params: {}};

        var deferred = $q.defer();
        $http.get(url, config).
            success(function (data) {
                deferred.resolve(data.data.publisher_groups);
            }).
            error(function (data) {
                deferred.reject(data);
            });
        return deferred.promise;
    }

    function download (accountId, publisherGroupId) {
        var url = '/api/accounts/' + accountId + '/publisher_groups/' + publisherGroupId + '/download/';
        $window.open(url, '_blank');
    }
});