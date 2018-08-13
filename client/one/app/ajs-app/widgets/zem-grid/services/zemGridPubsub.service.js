angular.module('one.widgets').factory('zemGridPubSub', function(NgZone) {
    //
    // Grid PubSub is an internal message chanel through which child directives and
    // services notifies each other about zem-grid specific events (e.g. scrolling, data updated, etc.)
    // It helps to reduce number of $watches, which boosts component performance.
    //

    var EVENTS = {
        BODY_HORIZONTAL_SCROLL: 'zem-grid-pubsub-bodyHorizontalScroll',
        BODY_VERTICAL_SCROLL: 'zem-grid-pubsub-bodyVerticalScroll',
        BODY_ROWS_UPDATED: 'zem-grid-pubsub-bodyRowsUpdated',
        METADATA_UPDATED: 'zem-grid-pubsub-metadataUpdated',
        DATA_UPDATED: 'zem-grid-pubsub-dataUpdated',

        EXT_SELECTION_UPDATED: 'zem-grid-ext-selection-updated',
        EXT_COLLAPSE_UPDATED: 'zem-grid-ext-collapse-updated',
        EXT_ORDER_UPDATED: 'zem-grid-ext-order-updated',
        EXT_COLUMNS_UPDATED: 'zem-grid-ext-columns-updated',
        EXT_NOTIFICATIONS_UPDATED: 'zem-grid-ext-notifications-updated',
    };

    function PubSub($scope) {
        this.EVENTS = EVENTS;

        this.register = register;
        this.notify = notify;

        function register(event, scope, listener) {
            var handler = $scope.$on(event, listener);
            scope = scope || $scope;
            scope.$on('$destroy', handler);
            return handler;
        }

        function notify(event, data) {
            NgZone.runOutsideAngular(function() {
                $scope.$broadcast(event, data);
            });
        }
    }

    return {
        createInstance: function(scope) {
            return new PubSub(scope);
        },
    };
});
