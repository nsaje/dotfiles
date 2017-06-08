angular.module('one.widgets').service('zemCloneAdGroupEndpoint', function ($q, $http) {
    this.clone = clone;

    function clone (adGroupId, config) {
        var url = '/rest/v1/adgroups/clone/',
            params = {
                adGroupId: adGroupId,
                destinationCampaignId: config.destinationCampaignId,
            };

        var deferred = $q.defer();
        $http.post(url, params)
            .then(function (data) {
                // TODO Using RESTAPI, convert fields to the right entity representation
                data.id = parseInt(data.id);
                data.parentId = parseInt(config.destinationCampaignId);
                deferred.resolve(data.data.data);
            })
            .catch(function (data) {
                deferred.reject(data.data.details);
            });

        return deferred.promise;
    }
});
