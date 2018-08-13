angular
    .module('one.services')
    .service('zemAgenciesEndpoint', function($http, $q) {
        this.getAgencies = getAgencies;

        var getAgenciesDeferred;
        function getAgencies() {
            if (!getAgenciesDeferred) {
                getAgenciesDeferred = $q.defer();
                var url = '/api/agencies/';
                var config = {
                    params: {},
                };
                $http
                    .get(url, config)
                    .success(function(data) {
                        getAgenciesDeferred.resolve(data);
                        getAgenciesDeferred = null;
                    })
                    .error(function(data) {
                        getAgenciesDeferred.reject(data);
                        getAgenciesDeferred = null;
                    });
            }

            return getAgenciesDeferred.promise;
        }
    });
