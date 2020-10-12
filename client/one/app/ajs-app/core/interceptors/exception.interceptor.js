angular
    .module('one.core')
    .factory('exceptionInterceptor', function(
        $q,
        $injector,
        zemExceptionHandlerService
    ) {
        function formatException(response) {
            var errorData =
                response.error || (response.data && response.data.data);
            var message;
            var errorCode;
            if (errorData) {
                message = errorData.details || errorData.message;
                errorCode = errorData.errorCode || errorData.error_code;
            }
            var requestMethod;
            var requestUrl;
            if (response.config) {
                requestMethod = response.config.method;
                requestUrl = response.config.url;
            }
            var exception = {
                message: message,
                errorCode: errorCode,
                headers: response.headers,
                status: response.status,
                method: requestMethod,
                url: requestUrl,
            };

            return exception;
        }

        function incrementRetryCounter(response) {
            response.config.previousRetries =
                (response.config.previousRetries || 0) + 1;
        }

        return {
            responseError: function(response) {
                if (
                    zemExceptionHandlerService.shouldRetryRequest(
                        formatException(response),
                        response.config.previousRetries
                    )
                ) {
                    var $http = $injector.get('$http');
                    var deferred = $q.defer();
                    incrementRetryCounter(response);

                    setTimeout(function() {
                        deferred.resolve(true);
                    }, zemExceptionHandlerService.getRequestRetryTimeout());

                    return deferred.promise.then(function() {
                        return $http(response.config);
                    });
                }

                zemExceptionHandlerService.handleHttpException(
                    formatException(response)
                );
                return $q.reject(response);
            },
        };
    });

angular.module('one.core').config(function($httpProvider) {
    $httpProvider.interceptors.push('exceptionInterceptor');
});
