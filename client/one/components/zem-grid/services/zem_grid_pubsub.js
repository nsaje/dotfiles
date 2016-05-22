/* globals oneApp */
'use strict';

oneApp.factory('zemGridPubSub', [function () {
    var EVENTS = {
        BODY_HORIZONTAL_SCROLL: 'zem-grid-pubsub-bodyHorizontalScroll',
        BODY_VERTICAL_SCROLL: 'zem-grid-pubsub-bodyVerticalScroll',
        METADATA_UPDATED: 'zem-grid-pubsub-metadataUpdated',
        DATA_UPDATED: 'zem-grid-pubsub-dataUpdated',
    };

    function PubSub (scope) {
        this.scope = scope;
        this.EVENTS = EVENTS;

        this.register = function (event, listener) {
            this.scope.$on(event, listener);
        };

        this.notify = function (event, data) {
            this.scope.$broadcast(event, data);
        };
    }

    function createInstance ($scope) {
        return new PubSub($scope);
    }

    return {
        createInstance: createInstance,
    };
}]);
