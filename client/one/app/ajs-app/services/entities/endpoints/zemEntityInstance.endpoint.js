angular
    .module('one.services')
    .service('zemEntityInstanceEndpoint', function(
        $http,
        $q,
        zemEntityConverter,
        zemUtils
    ) {
        //
        // Public API
        //
        this.create = create;
        this.get = get;
        this.update = update;

        function create(entityType, parentId, entityProperties) {
            var deferred = $q.defer();
            var url = getCreateUrl(entityType, parentId);
            var data =
                Object.keys(entityProperties).length === 0
                    ? null
                    : zemUtils.convertToUnderscore(entityProperties);

            $http
                .put(url, data)
                .success(function(data) {
                    deferred.resolve(data.data);
                })
                .error(function(data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        }

        function get(entityType, id) {
            var deferred = $q.defer();
            var url = getSettingsUrl(entityType, id);
            var config = {
                params: {},
            };

            $http
                .get(url, config)
                .success(function(data) {
                    if (!data || !data.data) {
                        deferred.reject(data);
                        return;
                    }
                    var convertedData = zemEntityConverter.convertSettingsFromApi(
                        entityType,
                        data.data
                    );
                    deferred.resolve(convertedData);
                })
                .error(function(data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        }

        function update(entityType, id, data) {
            var deferred = $q.defer();
            var url = getSettingsUrl(entityType, id);
            var config = {
                params: {},
            };

            var apiData = zemEntityConverter.convertSettingsToApi(
                entityType,
                data
            );

            $http
                .put(url, apiData, config)
                .success(function(res) {
                    var data = zemEntityConverter.convertSettingsFromApi(
                        entityType,
                        res.data
                    );
                    deferred.resolve(data);
                })
                .error(function(data, status) {
                    var errors;
                    if (
                        status === 400 &&
                        data &&
                        data.data.error_code === 'ValidationError'
                    ) {
                        errors = zemEntityConverter.convertValidationErrorsFromApi(
                            entityType,
                            data.data.errors
                        );
                    }
                    deferred.reject(errors);
                });
            return deferred.promise;
        }

        //
        // URL Mapping
        //
        var mapCreateUrls = {};
        mapCreateUrls[constants.entityType.ACCOUNT] = '/api/accounts/';
        mapCreateUrls[constants.entityType.CAMPAIGN] =
            '/api/accounts/$(id)/campaigns/';
        mapCreateUrls[constants.entityType.AD_GROUP] =
            '/api/campaigns/$(id)/ad_groups/';

        var mapSettingsUrls = {};
        mapSettingsUrls[constants.entityType.ACCOUNT] =
            '/api/accounts/$(id)/settings/';
        mapSettingsUrls[constants.entityType.CAMPAIGN] =
            '/api/campaigns/$(id)/settings/';
        mapSettingsUrls[constants.entityType.AD_GROUP] =
            '/api/ad_groups/$(id)/settings/';

        function getCreateUrl(entityType, id) {
            return mapCreateUrls[entityType].replace('$(id)', id);
        }

        function getSettingsUrl(entityType, id) {
            return mapSettingsUrls[entityType].replace('$(id)', id);
        }
    });
