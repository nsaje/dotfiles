angular.module('one.widgets').service('zemGeoTargetingEndpoint', function ($q, $http) {
    this.search = search;
    this.map = map;

    function search (searchTerm) {
        var REQUESTED_SIZE = 20;
        var url = '/rest/v1/geolocations/';

        var requests = {
            country: getDeferredPromise(
                url,
                {params: {nameContains: searchTerm, types: [constants.geolocationType.COUNTRY], limit: REQUESTED_SIZE}}
            ),
            region: getDeferredPromise(
                url,
                {params: {nameContains: searchTerm, types: [constants.geolocationType.REGION], limit: REQUESTED_SIZE}}
            ),
            dma: getDeferredPromise(
                url,
                {params: {nameContains: searchTerm, types: [constants.geolocationType.DMA], limit: REQUESTED_SIZE}}
            ),
            city: getDeferredPromise(
                url,
                {params: {nameContains: searchTerm, types: [constants.geolocationType.CITY], limit: REQUESTED_SIZE}}
            ),
        };

        return $q.all(requests).then(function (results) {
            return []
                .concat(results.country)
                .concat(results.region)
                .concat(results.dma)
                .concat(results.city);
        });
    }

    function map (keys) {
        var url = '/rest/v1/geolocations/';

        var batches = [];
        var BATCH_SIZE = 50;
        for (var i = 0; i < keys.length; i += BATCH_SIZE) {
            batches.push(keys.slice(i, i + BATCH_SIZE));
        }

        var requests = [];
        batches.forEach(function (batchKeys) {
            requests.push(getDeferredPromise(url, {params: {keys: batchKeys.join(','), limit: BATCH_SIZE}}));
        });

        return $q.all(requests).then(function (results) {
            // Flatten an array of arrays (results)
            return [].concat.apply([], results);
        });
    }

    function getDeferredPromise (url, config) {
        var deferred = $q.defer();
        $http.get(url, config)
            .then(function (data) {
                deferred.resolve(data.data.data);
            })
            .catch(function (data) {
                deferred.reject(data);
            });
        return deferred.promise;
    }
});
