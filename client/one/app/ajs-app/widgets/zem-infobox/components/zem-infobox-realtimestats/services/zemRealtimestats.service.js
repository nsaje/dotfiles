angular
    .module('one.widgets')
    .service('zemRealtimestatsService', function($q, zemRealtimestatsEndpoint) {
        // eslint-disable-line max-len

        // Public API
        this.getAdGroupSourcesStats = getAdGroupSourcesStats;

        function getAdGroupSourcesStats(adGroupId) {
            var deferred = $q.defer();

            zemRealtimestatsEndpoint
                .getAdGroupSourcesStats(adGroupId)
                .then(function(response) {
                    deferred.resolve(response.data.data);
                })
                .catch(function(response) {
                    deferred.reject(response.data);
                });

            return deferred.promise;
        }
    });
