/* globals oneApp */
'use strict';

oneApp.factory('zemGridObject', [function () {

    function Grid () {
        this.header = {
            element: null,
        };
        this.body = {
            element: null,
        };
        this.footer = {
            element: null,
        };

        this.meta = {
            source: null,
            breakdowns: null,
            levels: null,
            pubsub: null,
        };

        this.ui = {};
        this.ui.columnsWidths = [];
        this.ui.state = {
            headerRendered: false,
            bodyRendered: false,
            footerRendered: false,
            columnsWidthsCalculated: false,
        };
    }

    return {
        createInstance: function () {
            return new Grid();
        },
    };
}]);
