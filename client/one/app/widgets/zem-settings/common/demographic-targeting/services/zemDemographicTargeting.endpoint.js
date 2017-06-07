angular.module('one.widgets').service('zemDemographicTargetingEndpoint', function ($q, $http, zemUtils) {
    this.getReach = getReach;
    this.getTaxonomy = getTaxonomy;

    var REACH_CACHE = {};

    function getTaxonomy () {
        var url = '/rest/internal/bluekai/taxonomy/';

        var deferred = $q.defer();
        $http.get(url).then(function (data) {
            deferred.resolve(data.data.data);
        }).catch(function (data) {
            deferred.reject(data);
        });
        return deferred.promise;
    }

    function getReach (expression) {
        if (getReach.deferred) getReach.deferred.promise.abort();

        var cacheKey = JSON.stringify(expression);
        if (REACH_CACHE[cacheKey]) {
            return $q.resolve(REACH_CACHE[cacheKey]);
        }

        var url = '/rest/internal/bluekai/reach/';
        var deferred = zemUtils.createAbortableDefer();
        var httpConfig = {timeout: deferred.abortPromise};
        $http.post(url, expression, httpConfig).success(function (data) {
            var reach = {};
            reach.value = data.data.reach;
            reach.relative = getRelativeReach(reach.value);
            REACH_CACHE[cacheKey] = reach;
            deferred.resolve(reach);
        }).error(function (err) {
            deferred.reject(err);
        });

        getReach.deferred = deferred;
        return deferred.promise;
    }

    function getRelativeReach (reach) {
        var x = reach / 10000000;
        var relative  = 1 - (1 / (x + 1));
        return Math.round(relative * 100);
    }
});
