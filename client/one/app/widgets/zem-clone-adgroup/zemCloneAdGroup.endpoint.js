angular.module('one.widgets').service('zemCloneAdGroupEndpoint', function ($q, $http) {
    this.clone = clone;

    function clone (config) {
        var url = '/rest/v1/adgroups/clone/',
            params = {
                adGroupId: config.adGroupId,
                destinationCampaignId: config.destinationCampaignId,
            };

        var deferred = $q.defer();
        $http.post(url, params)
            .then(function (data) {
                deferred.resolve(data.data.data);
            })
            .catch(function (data) {
                deferred.reject(data.data.details);
            });

        return deferred.promise;
    }
});
