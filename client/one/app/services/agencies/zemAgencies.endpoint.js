angular.module('one.services').service('zemAgenciesEndpoint', function ($http, $q) {
    this.getAgencies = getAgencies;

    function getAgencies () {
        var deferred = $q.defer();
        var url = '/api/agencies/';
        var config = {
            params: {},
        };

        $http.get(url, config).
            success(function (data) {
                deferred.resolve(data);
            }).
            error(function (data) {
                deferred.reject(data);
            });

        return deferred.promise;
    }
});
