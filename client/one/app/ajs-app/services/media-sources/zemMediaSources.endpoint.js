angular
    .module('one.services')
    .service('zemMediaSourcesEndpoint', function($http, $q) {
        this.getSources = getSources;

        var getSourcesDeferred;
        var getSourcesConfig;
        function getSources() {
            var newConfig = {
                params: {},
            };

            if (
                !getSourcesDeferred ||
                !angular.equals(getSourcesConfig, newConfig)
            ) {
                getSourcesDeferred = $q.defer();
                getSourcesConfig = newConfig;

                var url = '/api/sources/';
                $http
                    .get(url, getSourcesConfig)
                    .success(function(data) {
                        getSourcesDeferred.resolve(data);
                        getSourcesDeferred = null;
                    })
                    .error(function(data) {
                        getSourcesDeferred.reject(data);
                        getSourcesDeferred = null;
                    });
            }

            return getSourcesDeferred.promise;
        }
    });
