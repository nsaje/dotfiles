require('./zemToasts.component.less');

angular.module('one.widgets').component('zemToasts', {
    template: require('./zemToasts.component.html'),
    controller: function($timeout, zemToastsService) {
        var $ctrl = this;

        var CLEAR_TOAST_TIMEOUT = 200;

        $ctrl.toasts = [];
        $ctrl.getToastClasses = getToastClasses;
        $ctrl.clearToast = clearToast;

        $ctrl.$onInit = function() {
            zemToastsService.onToast(addToast);
        };

        function addToast(event, toast) {
            $ctrl.toasts.push(toast);
            if (toast.options && toast.options.timeout) {
                $timeout(function() {
                    clearToast(toast);
                }, toast.options.timeout);
            }
        }

        function getToastClasses(toast) {
            var classes = [];
            classes.push('toasts__item--' + toast.type);
            if (toast.clearing) {
                classes.push('toasts__item--animate-clear');
            }
            return classes;
        }

        function clearToast(toast) {
            if (toast.clearing) return;
            toast.clearing = true;
            $timeout(function() {
                removeToast(toast);
            }, CLEAR_TOAST_TIMEOUT);
        }

        function removeToast(toast) {
            var idx = $ctrl.toasts.indexOf(toast);
            if (idx >= 0) {
                $ctrl.toasts.splice(idx, 1);
            }
        }
    },
});
