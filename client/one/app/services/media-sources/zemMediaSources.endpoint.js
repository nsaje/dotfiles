angular.module('one.services').service('zemMediaSourcesEndpoint', function ($http, $q, zemDataFilterService) { // eslint-disable-line max-len
    this.getSources = getSources;

    function getSources () {
        var deferred = $q.defer();
        var url = '/api/sources/';
        var config = {
            params: {},
        };

        if (zemDataFilterService.getShowArchived()) {
            config.params.show_archived = true;
        }

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
