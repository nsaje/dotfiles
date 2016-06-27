/* globals oneApp */
'use strict';

oneApp.factory('zemGridPubSub', [function () {

    //
    // Grid PubSub is an internal message chanel through which child directives and
    // services notifies each other about zem-grid specific events (e.g. scrolling, data updated, etc.)
    // It helps to reduce number of $watches, which boosts component performance.
    //

    var EVENTS = {
        BODY_HORIZONTAL_SCROLL: 'zem-grid-pubsub-bodyHorizontalScroll',
        BODY_VERTICAL_SCROLL: 'zem-grid-pubsub-bodyVerticalScroll',
        METADATA_UPDATED: 'zem-grid-pubsub-metadataUpdated',
        DATA_UPDATED: 'zem-grid-pubsub-dataUpdated',
    };

    function PubSub (scope) {
        this.EVENTS = EVENTS;

        this.register = register;
        this.notify = notify;

        function register (event, listener) {
            return scope.$on(event, listener);
        }

        function notify (event, data) {
            scope.$broadcast(event, data);
        }
    }

    return {
        createInstance: function (scope) {
            return new PubSub(scope);
        },
    };
}]);
