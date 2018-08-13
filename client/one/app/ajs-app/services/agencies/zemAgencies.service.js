angular
    .module('one.services')
    .service('zemAgenciesService', function(
        $http,
        $q,
        zemAgenciesEndpoint,
        zemPubSubService
    ) {
        // eslint-disable-line max-len
        this.getAgencies = getAgencies;

        this.onAgenciesUpdate = onAgenciesUpdate;

        var pubSub = zemPubSubService.createInstance();
        var EVENTS = {
            ON_AGENCIES_UPDATE: 'zem-agencies-service-on-agencies-update',
        };

        var agencies;

        function getAgencies(reload) {
            var deferred = $q.defer();

            if (!reload && agencies) {
                deferred.resolve(agencies);
            } else {
                loadAgencies().then(function() {
                    deferred.resolve(agencies);
                });
            }

            return deferred.promise;
        }

        function onAgenciesUpdate(callback) {
            return pubSub.register(EVENTS.ON_AGENCIES_UPDATE, callback);
        }

        function loadAgencies() {
            return zemAgenciesEndpoint.getAgencies().then(function(data) {
                agencies = data.data.agencies;
                pubSub.notify(EVENTS.ON_AGENCIES_UPDATE, agencies);
            });
        }
    });
