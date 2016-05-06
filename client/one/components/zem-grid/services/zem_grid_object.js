/* globals oneApp */
'use strict';

oneApp.factory('zemGridObject', [function () {

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
    }

    return {
        createInstance: function () {
            return new Grid();
        },
    };
}]);
