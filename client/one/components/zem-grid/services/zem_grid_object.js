/* globals oneApp */
'use strict';

oneApp.factory('zemGridObject', ['$rootScope', function ($rootScope) {

    function Grid () {
        this.header = {};
        this.body = {};
        this.footer = {};
        this.ui = {};

        this.meta = {
            source: null,
            breakdowns: null,
            levels: null,
        };

        this.registerListener = function (event, listener) {
            // FIXME: Replace AngularJS PubSub with better solution (observables)
            return $rootScope.$on(event, listener);
        };

        this.notifyListeners = function (event, data) {
            $rootScope.$emit(event, data);
        };
    }

    return {
        createInstance: function () {
            return new Grid();
        },
    };
}]);
