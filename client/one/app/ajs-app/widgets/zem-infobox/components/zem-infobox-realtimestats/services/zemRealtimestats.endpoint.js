angular
    .module('one.widgets')
    .service('zemRealtimestatsEndpoint', function($http) {
        this.getAdGroupSourcesStats = getAdGroupSourcesStats;

        function getAdGroupSourcesStats(adGroupId) {
            var url =
                '/rest/internal/adgroups/' +
                adGroupId +
                '/realtimestats/sources/';
            return $http.get(url);
        }
    });
