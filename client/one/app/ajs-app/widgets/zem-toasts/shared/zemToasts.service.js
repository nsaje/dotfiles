angular
    .module('one.services')
    .service('zemToastsService', function($timeout, zemPubSubService) {
        // eslint-disable-line max-len
        this.info = info;
        this.success = success;
        this.warning = warning;
        this.error = error;
        this.onToast = onToast;

        var pubSub = zemPubSubService.createInstance();
        var EVENTS = {
            ON_NEW_TOAST: 'zem-toasts-service-on-change',
        };

        function info(message, options) {
            var toast = {
                type: constants.notificationType.info,
                message: message,
                options: options,
            };

            addToast(toast, options);
        }

        function success(content, options) {
            var toast = {
                type: constants.notificationType.success,
                content: content,
                options: options,
            };

            addToast(toast, options);
        }

        function warning(content, options) {
            var toast = {
                type: constants.notificationType.warning,
                content: content,
                options: options,
            };

            addToast(toast, options);
        }

        function error(content, options) {
            var toast = {
                type: constants.notificationType.danger,
                content: content,
                options: options,
            };

            addToast(toast, options);
        }

        function addToast(toast) {
            if (typeof toast.content === 'string') {
                toast.content = {
                    message: toast.content,
                };
            }
            pubSub.notify(EVENTS.ON_NEW_TOAST, toast);
        }

        function onToast(callback) {
            return pubSub.register(EVENTS.ON_NEW_TOAST, callback);
        }
    });
