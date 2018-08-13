angular
    .module('one.widgets')
    .service('zemDemoRequestService', function($q, zemDemoRequestEndpoint) {
        // eslint-disable-line max-len
        this.requestDemo = requestDemo;

        function requestDemo() {
            var deferred = $q.defer();
            zemDemoRequestEndpoint
                .requestDemo()
                .then(function(response) {
                    var data = {
                        url: response.data.data.url,
                        password: response.data.data.password,
                    };
                    deferred.resolve(data);
                })
                .catch(function(response) {
                    var errorMessage =
                        response && response.message ? response.message : null;
                    deferred.reject(errorMessage);
                });
            return deferred.promise;
        }
    });
