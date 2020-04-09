angular
    .module('one.common')
    .service('zemPublisherGroupTargetingEndpoint', function($q, $http) {
        this.list = list;

        function list(accountId, agencyId, notImplicit) {
            var url = '/api/publisher_groups/';
            var config = {
                params: {
                    not_implicit: notImplicit,
                    agency_id: agencyId,
                    account_id: accountId,
                },
            };

            var deferred = $q.defer();
            $http
                .get(url, config)
                .then(function(data) {
                    deferred.resolve(data.data.data.publisher_groups);
                })
                .catch(function(data) {
                    deferred.reject(data);
                });
            return deferred.promise;
        }
    });
