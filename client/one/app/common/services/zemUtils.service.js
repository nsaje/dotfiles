angular.module('one.services').service('zemUtils', function ($q) { // eslint-disable-line max-len

    this.convertToCamelCase = convertToCamelCase;
    this.convertToUnderscore = convertToUnderscore;
    this.createAbortableDefer = createAbortableDefer;

    function convertToCamelCase (obj) {
        if (!(obj instanceof Object)) return obj;
        if (obj instanceof Array) return obj.map(convertToCamelCase);

        var convertedObj = {};
        Object.keys(obj).forEach(function (key) {
            var convertedKey = key.replace(/(_[a-z])/g, function ($1) { return $1.toUpperCase().replace('_', ''); });
            var value = convertToCamelCase(obj[key]);
            convertedObj[convertedKey] = value;
        });
        return convertedObj;
    }

    function convertToUnderscore (obj) {
        if (!(obj instanceof Object)) return obj;
        if (obj instanceof Date) return obj;
        if (obj instanceof Array) return obj.map(convertToUnderscore);

        var convertedObj = {};
        Object.keys(obj).forEach(function (key) {
            var convertedKey = key.replace(/([A-Z])/g, function ($1) { return '_' + $1.toLowerCase(); });
            var value = convertToUnderscore(obj[key]);
            convertedObj[convertedKey] = value;
        });
        return convertedObj;
    }

    function createAbortableDefer () {
        var deferred = $q.defer();
        var deferredAbort = $q.defer();
        deferred.promise.abort = function () {
            deferredAbort.resolve();
        };
        deferred.promise.finally(
            function () {
                deferred.promise.abort = angular.noop;
            }
        );

        deferred.abortPromise = deferredAbort.promise;
        return deferred;
    }

});
