angular.module('one.services').service('zemUtils', function ($q) { // eslint-disable-line max-len

    this.convertToCamelCase = convertToCamelCase;
    this.convertToUnderscore = convertToUnderscore;
    this.convertToElementName = convertToElementName;
    this.createAbortableDefer = createAbortableDefer;
    this.traverseTree = traverseTree;
    this.shouldOpenInNewTab = shouldOpenInNewTab;
    this.intersects = intersects;

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
            var convertedKey = key.replace(/[A-Z]+/g, function (match, offset) {
                return (offset > 0 ? '_' : '') + match.toLowerCase();
            });
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

    function convertToElementName (componentName) {
        // zemSomeComponent --> zem-some-component
        var tagName = componentName.replace(/([A-Z])/g, function ($1) { return '-' + $1.toLowerCase(); });
        if (tagName[0] === '-') tagName = tagName.substring(1);
        return tagName;
    }

    function traverseTree (root, callback) {
        var queue = [root];
        var n;

        while (queue.length > 0) {

            n = queue.shift();
            callback(n);

            if (!n.childNodes) {
                continue;
            }

            for (var i = 0; i < n.childNodes.length; i++) {
                queue.push(n.childNodes[i]);
            }
        }
    }

    function shouldOpenInNewTab (event) {
        // Has user clicked with middle mouse button or while ctrl/cmd keys were pressed
        return event.ctrlKey || event.metaKey || event.which === 2;
    }

    function intersects (array1, array2) {
        // Simple solution for finding if arrays are having common element
        return array1.filter(function (n) {
            return array2.indexOf(n) !== -1;
        }).length > 0;
    }
});
