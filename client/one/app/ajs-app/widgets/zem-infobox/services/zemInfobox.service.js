angular
    .module('one.widgets')
    .service('zemInfoboxService', function(zemInfoboxEndpoint, $q) {
        this.reloadInfoboxData = reloadInfoboxData;

        function reloadInfoboxData(entity) {
            var deferred = $q.defer();

            if (entity === undefined) {
                deferred.reject();
            } else {
                zemInfoboxEndpoint
                    .getInfoboxData(entity)
                    .then(function(data) {
                        deferred.resolve(data);
                    })
                    .catch(function(error) {
                        deferred.reject(error);
                    });
            }

            return deferred.promise;
        }
    });
