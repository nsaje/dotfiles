angular
    .module('one.services')
    .service('zemAlertsService', function(zemAlertsEndpoint, zemPubSubService) {
        // eslint-disable-line max-len
        this.notify = notify;
        this.getAlerts = getAlerts;
        this.refreshAlerts = refreshAlerts;
        this.onAlertsChange = onAlertsChange;

        var alerts = [];

        var pubSub = zemPubSubService.createInstance();
        var EVENTS = {
            ON_ALERTS_CHANGE: 'zem-alerts-service-on-change',
        };

        function notify(type, message, closeable) {
            var alert = {
                type: type,
                message: message,
            };

            if (closeable) {
                alert.close = function() {
                    closeAlert(alert);
                    alert.close = angular.noop;
                };
            }

            alerts.push(alert);
        }

        function closeAlert(alert) {
            var idx = alerts.indexOf(alert);
            if (idx >= 0) {
                alerts.splice(idx, 1);
            }
            pubSub.notify(EVENTS.ON_ALERTS_CHANGE);
        }

        function getAlerts() {
            return alerts;
        }

        function refreshAlerts(level, entityId) {
            alerts = [];
            zemAlertsEndpoint.getAlerts(level, entityId).then(function(result) {
                if (result.data && result.data.data) {
                    alerts = result.data.data.alerts.concat(alerts);
                }
                pubSub.notify(EVENTS.ON_ALERTS_CHANGE);
            });
        }

        function onAlertsChange(callback) {
            return pubSub.register(EVENTS.ON_ALERTS_CHANGE, callback);
        }
    });
