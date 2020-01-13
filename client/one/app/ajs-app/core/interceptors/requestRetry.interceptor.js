var APP_CONFIG = require('../../../app.config').APP_CONFIG;

// This HTTP interceptor retries to send a HTTP request in case it receives a HTTP error with a particular code
// The list of HTTP status codes which trigger a retry are specified in the app.config variable httpStatusCodesForRequestRetry
// The maximum number of requests that can be called is specified in the app.config variable maxRequestRetries
angular
    .module('one.core')
    .factory('requestRetryInterceptor', function($q, $injector) {
        return {
            responseError: function(response) {
                if (
                    APP_CONFIG.httpStatusCodesForRequestRetry.indexOf(
                        response.status
                    ) !== -1
                ) {
                    if (response.config.retries === undefined) {
                        response.config.retries = 1; // If this is the first request, initialize retry counter
                    }

                    // Retry if max number of retries has not been surpassed yet
                    if (
                        response.config.retries < APP_CONFIG.maxRequestRetries
                    ) {
                        response.config.retries = response.config.retries + 1;

                        var $http = $injector.get('$http');
                        return $http(response.config);
                    }
                }

                // Status code was incorrect or number of retries was surpassed, stop trying.
                return $q.reject(response);
            },
        };
    });

angular.module('one.core').config(function($httpProvider) {
    $httpProvider.interceptors.push('requestRetryInterceptor');
});
