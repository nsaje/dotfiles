angular.module('one.widgets').service('zemDemographicTargetingEndpoint', function ($q, $http, zemUtils) {
    this.getReach = getReach;
    this.getTaxonomy = getTaxonomy;

    var REACH_CACHE = {};

    function getTaxonomy () {
        var url = '/rest/internal/bluekai/taxonomy/';
        return getDeferredPromise(url);
    }

    function getReach (expression) {
        // FIXME: Only for DEBUGGING purposes
        if (getReach.deferred) getReach.deferred.promise.abort();
        getReach.deferred = zemUtils.createAbortableDefer();

        if (REACH_CACHE[expression]) {
            return $q.resolve(REACH_CACHE[expression]);
        }

        var t = setTimeout(function () {
            var data = {};
            data.value = Math.round(Math.random() * 5 * Math.pow(10, 9));
            data.relative = getRelativeReach(data.value);

            REACH_CACHE[expression] = data;
            getReach.deferred.resolve(data);
        }, 1000);

        getReach.deferred.abortPromise.then(function () {
            clearTimeout(t);
        });

        return getReach.deferred.promise;
    }

    function getRelativeReach (reach) {
        var mid = Math.pow(10, 9);
        var max = 5 * Math.pow(10, 9);
        if (reach > mid) {
            return 50 + Math.ceil((reach - mid) / (max - mid) * 100 / 2);
        }

        return Math.ceil(reach / mid * 100 / 2);
    }

    function getDeferredPromise (url, config) {
        var deferred = $q.defer();
        $http.get(url, config).then(function (data) {
            deferred.resolve(data.data.data);
        }).catch(function (data) {
            deferred.reject(data);
        });
        return deferred.promise;
    }
});
