angular
    .module('one.widgets')
    .service('zemAdGroupSourcesEndpoint', function($q, $http, zemUtils) {
        //eslint-disable-line max-len
        this.create = create;
        this.list = list;

        function list(id, config) {
            config = convertConfig(config);
            var url = '/api/ad_groups/' + id + '/sources/';

            var deferred = $q.defer();
            $http
                .get(url, config)
                .success(function(data) {
                    var converted = zemUtils.convertToCamelCase(data.data);
                    deferred.resolve(converted);
                })
                .error(function(data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        }

        function convertConfig(config) {
            var converted = {params: {}};
            if (!config) return converted;

            if (config.filteredSources.length > 0) {
                converted.params.filtered_sources = config.filteredSources.join(
                    ','
                );
            }

            return converted;
        }

        function create(adGroupId, sourceId) {
            var deferred = $q.defer();
            var url = '/api/ad_groups/' + adGroupId + '/sources/';

            var data = {
                source_id: sourceId,
            };

            $http
                .put(url, data)
                .success(function(data) {
                    deferred.resolve(data);
                })
                .error(function(data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        }
    });
