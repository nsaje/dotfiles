/* globals oneApp */
'use strict';

oneApp.factory('zemGridPubSub', [function () {

    // PubSub that hides AngularJS scope events mechanism and
    // provides some simplifications over it (debouncing, etc.)
    // and removes the need for child directives to work with scopes.

    var EVENTS = {
        BODY_HORIZONTAL_SCROLL: 'zem-grid-pubsub-bodyHorizontalScroll',
        BODY_VERTICAL_SCROLL: 'zem-grid-pubsub-bodyVerticalScroll',
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
