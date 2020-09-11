angular
    .module('one.widgets')
    .service('zemScheduledReportsEndpoint', function($q, $http, zemUtils) {
        this.list = list;
        this.remove = remove;

        function list(entity) {
            var url;
            if (entity === null) {
                url = '/api/scheduled_reports/';
            } else if (entity.type === constants.entityType.ACCOUNT) {
                url = 'api/scheduled_reports/?account_id=' + entity.id;
            }

            var deferred = $q.defer();
            $http
                .get(url)
                .then(function(data) {
                    deferred.resolve(
                        zemUtils.convertToCamelCase(data.data.data.reports)
                    );
                })
                .catch(function(error) {
                    deferred.reject(error);
                });

            return deferred.promise;
        }

        function remove(id) {
            var url = '/api/scheduled_reports/' + id + '/';

            var deferred = $q.defer();
            $http
                .delete(url)
                .then(function() {
                    deferred.resolve();
                })
                .catch(function(error) {
                    deferred.reject(error);
                });

            return deferred.promise;
        }
    });
