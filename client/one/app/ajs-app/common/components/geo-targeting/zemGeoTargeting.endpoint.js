angular
    .module('one.common')
    .service('zemGeoTargetingEndpoint', function($q, $http) {
        this.search = search;
        this.searchByTypes = searchByTypes;
        this.map = map;
        this.mapKey = mapKey;

        function search(searchTerm) {
            var requests = {
                country: searchByTypes(searchTerm, [
                    constants.geolocationType.COUNTRY,
                ]),
                region: searchByTypes(searchTerm, [
                    constants.geolocationType.REGION,
                ]),
                dma: searchByTypes(searchTerm, [constants.geolocationType.DMA]),
                city: searchByTypes(searchTerm, [
                    constants.geolocationType.CITY,
                ]),
            };

            return $q.all(requests).then(function(results) {
                return []
                    .concat(results.country)
                    .concat(results.region)
                    .concat(results.dma)
                    .concat(results.city);
            });
        }

        function map(keys) {
            var url = '/rest/v1/geolocations/';

            var batches = [];
            var BATCH_SIZE = 50;
            for (var i = 0; i < keys.length; i += BATCH_SIZE) {
                batches.push(keys.slice(i, i + BATCH_SIZE));
            }

            var requests = [];
            batches.forEach(function(batchKeys) {
                requests.push(
                    getDeferredPromise(url, {
                        params: {keys: batchKeys.join(','), limit: BATCH_SIZE},
                    })
                );
            });

            return $q.all(requests).then(function(results) {
                // Flatten an array of arrays (results)
                return [].concat.apply([], results);
            });
        }

        function mapKey(key) {
            var deferred = $q.defer();
            map([key]).then(function(result) {
                deferred.resolve(result[0]);
            });
            return deferred.promise;
        }

        function searchByTypes(searchTerm, locationTypes) {
            var url = '/rest/v1/geolocations/';
            var REQUESTED_SIZE = 20;
            return getDeferredPromise(url, {
                params: {
                    nameContains: searchTerm,
                    types: locationTypes,
                    limit: REQUESTED_SIZE,
                },
            });
        }

        function getDeferredPromise(url, config) {
            var deferred = $q.defer();
            $http
                .get(url, config)
                .then(function(data) {
                    deferred.resolve(data.data.data);
                })
                .catch(function(data) {
                    deferred.reject(data);
                });
            return deferred.promise;
        }
    });
