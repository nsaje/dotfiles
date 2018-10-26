angular
    .module('one.widgets')
    .service('zemGridBulkPublishersActionsEndpoint', function($http, $q) {
        this.bulkUpdate = bulkUpdate;

        function bulkUpdate(config) {
            var defer = $q.defer();

            var url = '/api/publishers/targeting/';
            $http
                .post(url, config)
                .success(function(data) {
                    defer.resolve(data);
                    defer = null;
                })
                .error(function(data) {
                    defer.reject(data);
                    defer = null;
                });

            return defer.promise;
        }
    });
