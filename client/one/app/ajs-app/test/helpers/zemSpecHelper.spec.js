window.zemSpecsHelper = new zemSpecsHelperProvider(); // eslint-disable-line no-unused-vars
function zemSpecsHelperProvider() {
    this.getMockedAsyncFunction = getMockedAsyncFunction;

    function getMockedAsyncFunction($injector, data, reject) {
        return function() {
            var $q = $injector.get('$q');
            var deferred = $q.defer();
            if (reject) {
                deferred.reject(data);
            } else {
                deferred.resolve(data);
            }
            return deferred.promise;
        };
    }
}
