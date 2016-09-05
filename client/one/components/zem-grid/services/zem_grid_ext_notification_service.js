/* globals angular */
'use strict';

angular.module('one.legacy').factory('zemGridNotificationService', [function () { // eslint-disable-line max-len

    function NotificationService (grid) {
        var pubsub = grid.meta.pubsub;
        var notifications = [];

        this.notify = notify;
        this.getNotifications = getNotifications;

        function getNotifications () {
            return notifications;
        }

        function notify (type, message) {
            var notification = {
                type: type,
                message: message,
            };

            notification.close = function () {
                closeNotification(notification);
                notification.close = angular.noop;
            };

            notifications.push(notification);
            pubsub.notify(pubsub.EVENTS.EXT_NOTIFICATIONS_UPDATED);
            return notification;
        }

        function closeNotification (notification) {
            var idx = notifications.indexOf(notification);
            if (idx >= 0) {
                notifications.splice(idx, 1);
            }
            pubsub.notify(pubsub.EVENTS.EXT_NOTIFICATIONS_UPDATED);
        }
    }

    return {
        createInstance: function (grid) {
            return new NotificationService(grid);
        }
    };
}]);
