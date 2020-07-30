var constantsHelpers = require('../../../../shared/helpers/constants.helpers');

angular
    .module('one.services')
    .service('zemEntityActionsEndpoint', function($http, $q, config) {
        // eslint-disable-line max-len

        var METHOD_PUT = 'PUT';

        var apiRestEntityUrlMapping = {};
        apiRestEntityUrlMapping[constants.entityType.ACCOUNT] =
            config.apiRestInternalUrl + '/accounts/${id}';
        apiRestEntityUrlMapping[constants.entityType.CAMPAIGN] =
            config.apiRestInternalUrl + '/campaigns/${id}';
        apiRestEntityUrlMapping[constants.entityType.AD_GROUP] =
            config.apiRestInternalUrl + '/adgroups/${id}';

        //
        // Public API
        //
        this.archive = archive;
        this.restore = restore;
        this.activate = activate;
        this.deactivate = deactivate;

        function activate(entityType, id) {
            var url = apiRestEntityUrlMapping[entityType].replace('${id}', id);
            return request(METHOD_PUT, url, {
                state: constantsHelpers.convertToName(
                    constants.settingsState.ACTIVE,
                    constants.settingsState
                ),
            });
        }

        function deactivate(entityType, id) {
            var url = apiRestEntityUrlMapping[entityType].replace('${id}', id);
            return request(METHOD_PUT, url, {
                state: constantsHelpers.convertToName(
                    constants.settingsState.INACTIVE,
                    constants.settingsState
                ),
            });
        }

        function archive(entityType, id) {
            var url = apiRestEntityUrlMapping[entityType].replace('${id}', id);
            return request(METHOD_PUT, url, {archived: true});
        }

        function restore(entityType, id) {
            var url = apiRestEntityUrlMapping[entityType].replace('${id}', id);
            return request(METHOD_PUT, url, {archived: false});
        }

        function request(method, url, data, config) {
            if (!url) throw new Error('Action Not Supported: ' + url);
            data = data || {};
            config = config || {params: {}};

            var httpConfig = {
                method: method,
                url: url,
                data: data,
            };

            Object.assign(httpConfig, config);

            var deferred = $q.defer();
            $http(httpConfig)
                .success(function(data) {
                    deferred.resolve(data);
                })
                .error(function(data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        }
    });
