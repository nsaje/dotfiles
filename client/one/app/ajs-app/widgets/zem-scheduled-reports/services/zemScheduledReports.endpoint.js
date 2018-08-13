angular
    .module('one.widgets')
    .service('zemScheduledReportsEndpoint', function(
        $q,
        $http,
        zemUtils,
        zemPermissions
    ) {
        this.list = list;
        this.remove = remove;

        function list(entity) {
            var url;
            if (entity === null) {
                if (
                    zemPermissions.hasPermission(
                        'zemauth.can_see_new_report_schedule'
                    )
                ) {
                    url = '/api/scheduled_reports/';
                } else {
                    url = '/api/all_accounts/reports/';
                }
            } else if (entity.type === constants.entityType.ACCOUNT) {
                if (
                    zemPermissions.hasPermission(
                        'zemauth.can_see_new_report_schedule'
                    )
                ) {
                    url = 'api/scheduled_reports/?account_id=' + entity.id;
                } else {
                    url = '/api/accounts/' + entity.id + '/reports/';
                }
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
            var url;
            if (
                zemPermissions.hasPermission(
                    'zemauth.can_see_new_report_schedule'
                )
            ) {
                url = '/api/scheduled_reports/' + id + '/';
            } else {
                url = '/api/accounts/reports/remove/' + id;
            }

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
