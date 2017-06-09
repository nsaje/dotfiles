angular.module('one.widgets').service('zemCloneContentEndpoint', function ($q, $http) {
    this.clone = clone;

    function clone (config) {
        var url = '/rest/internal/contentads/batch/clone/',
            params = convertToApi(config);

        var deferred = $q.defer();
        $http.post(url, params)
            .then(function (data) {
                deferred.resolve(data.data.data);
            })
            .catch(function (data) {
                deferred.reject(convertErrorsFromApi(data));
            });

        return deferred.promise;
    }

    function convertToApi (config) {
        var converted = {
            adGroupId: config.adGroupId,
            batchId: config.selection.filterId,
            contentAdIds: config.selection.selectedIds,
            deselectedContentAdIds: config.selection.unselectedIds,
            destinationAdGroupId: config.destinationAdGroupId,
            destinationBatchName: config.destinationBatchName,
        };

        if (converted.state !== null) {
            var state = config.state ? constants.settingsState.ACTIVE : constants.settingsState.INACTIVE;
            converted.state = constants.convertToName(state, constants.settingsState);
        }

        return converted;
    }

    function convertErrorsFromApi (data) {
        return {
            destinationAdGroupId: data.data.destinationAdGroupId ? data.data.destinationAdGroupId[0] : null,
            destinationBatchName: data.data.destinationBatchName ? data.data.destinationBatchName[0] : null,
            message: data.status === 500 ? 'Something went wrong' : null,
        };
    }
});
