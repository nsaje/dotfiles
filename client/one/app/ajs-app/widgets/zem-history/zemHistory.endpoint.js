angular
    .module('one.widgets')
    .service('zemHistoryEndpoint', function($q, $http, zemUtils) {
        this.getHistory = getHistory;

        function getHistory(entityId, entityType, order) {
            var url = '/api/history/';
            var params = generateGetHistoryParams(entityId, entityType, order);

            var deferred = $q.defer();
            $http
                .get(url, {params: params})
                .then(function(data) {
                    deferred.resolve(
                        zemUtils.convertToCamelCase(data.data.data.history)
                    );
                })
                .catch(function(error) {
                    deferred.reject(error);
                });

            return deferred.promise;
        }

        function generateGetHistoryParams(entityId, entityType, order) {
            var params = {};

            switch (entityType) {
                case constants.entityType.AD_GROUP:
                    params = {
                        ad_group: entityId,
                        level: constants.historyLevel.AD_GROUP,
                    };
                    break;
                case constants.entityType.CAMPAIGN:
                    params = {
                        campaign: entityId,
                        level: constants.historyLevel.CAMPAIGN,
                    };
                    break;
                case constants.entityType.ACCOUNT:
                    params = {
                        account: entityId,
                        level: constants.historyLevel.ACCOUNT,
                    };
                    break;
            }

            if (order) {
                params.order = order
                    .replace('changedBy', 'created_by')
                    .replace('datetime', 'created_dt');
            }

            return params;
        }
    });
