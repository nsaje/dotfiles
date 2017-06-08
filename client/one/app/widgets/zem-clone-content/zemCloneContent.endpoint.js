angular.module('one.widgets').service('zemCloneContentEndpoint', function ($q, $http) {
    this.clone = clone;

    function clone (config) {
        var url = '/rest/internal/contentads/batch/clone/',
            params = {
                adGroupId: config.adGroupId,
                batchId: config.selection.filterId,
                contentAdIds: config.selection.selectedIds,
                deselectedContentAdIds: config.selection.unselectedIds,
                destinationAdGroupId: config.destinationAdGroupId,
                state: config.state,
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
