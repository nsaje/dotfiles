/* globals oneApp */
'use strict';

oneApp.factory('zemGridObject', [function () {

    //
    // This service defines Grid object. It is the main
    // data structure holding entire Grid state that is passed
    // to the Grid directives and services.
    //
    // This service defines empty grid state and its artifacts
    // and document all for easier reasoning.
    //
    // TODO: refactor, docs needed
    //

    //
    //  Grid
    //      header - columns
    //      body - rows (type, stats, etc.)
    //      footer - stats
    //      $ui - ui related stuff
    //      $data - data related stuff
    //      $meta - services, etc.
    //

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
