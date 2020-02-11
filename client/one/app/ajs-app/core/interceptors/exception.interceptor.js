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
            var exception = {
                message: message,
                errorCode: errorCode,
                headers: response.headers,
                status: response.status,
            };

            return exception;
        }

        function incrementAttemptCounter(response) {
            response.config.previousAttempts =
                (response.config.previousAttempts || 0) + 1;
        }

        function retryRequestIfNecessary(response) {
            var retrying = false;

            if (
                zemExceptionHandlerService.shouldRetryRequest(
                    formatException(response),
                    response.config.previousAttempts
                )
            ) {
                incrementAttemptCounter(response);

                // Trigger a repeated request after a set timeout
                setTimeout(function() {
                    var $http = $injector.get('$http');
                    $http(response.config);
                }, zemExceptionHandlerService.getRequestRetryTimeout());
                retrying = true;
            }

            return retrying;
        }

        return {
            responseError: function(response) {
                var retrying = retryRequestIfNecessary(response);

                if (!retrying) {
                    // We did not retry => handle exception and cancel request
                    zemExceptionHandlerService.handleHttpException(
                        formatException(response)
                    );

                    return $q.reject(response);
                }
            },
        };
    });

angular.module('one.core').config(function($httpProvider) {
    $httpProvider.interceptors.push('exceptionInterceptor');
});
