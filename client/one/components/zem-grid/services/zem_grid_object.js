/* globals oneApp */
'use strict';

oneApp.factory('zemGridObject', ['zemGridConstants', function (zemGridConstants) {

    //
    // This service defines Grid object. It is the main
    // data structure holding entire Grid state that is passed
    // to the Grid directives and services.
    //
    // This service defines empty grid state and its artifacts
    // and document all for easier reasoning.
    //

    function Grid () {
        this.header = {         // zem-grid header
            columns: [],        // array of visible columns (atm. subset of meta.data.columns)
            ui: createUiObject(),
        };
        this.body = {           // zem-grid body
            rows: [],           // flatten DataSource data (breakdown tree); see createRow() for row fields def.
            ui: createUiObject(),
        };
        this.footer = {         // zem-grid footer
            row: null,          // footer is actually one special row
            ui: createUiObject(),
        };

        this.meta = {           // meta information and functionality
            api: null,          // zemGridApi - api for exposed/public zem-grid functionality
            service: null,      // zemGridDataService - access to data
            pubsub: null,       // zemGridPubSub - internal message queue
            data: null,         // meta-data retrieved through Endpoint - columns definitions
            scope: null,        // zem-grid scope used for running $digest and $emit internally
        };

        this.ui = {
            element: null,      // zem-grid dom element
            columnsWidths: [],  // columns widths used by grid cells
        };
    }

    function createUiObject () {
        return {
            element: null,      // DOM element of corresponded grid component
        };
    }

    function createGrid () {
        return new Grid();
    }

    function createRow (type, data, level, parent) {
        return {
            type: type,         // Type of a row (STATS, BREAKDOWN)
            data: data,         // Data that corresponds to this row (stats or breakdown object - see DataSource)
            level: level,       // Level of data in breakdown tree which this row represents
            parent: parent,     // Parent row - row on which breakdown has been made
            collapsed: false,   // Collapse flag used by collapsing feature
            visible: true,      // Visibility flag - row can be hidden for different reasons (e.g. collapsed parent)
        };
    }

    function createColumn (data) {
        return {
            field: data.field,
            data: data,
            visible: true,
        };
    }

    return {
        createGrid: createGrid,
        createRow: createRow,
        createColumn: createColumn,
    };
}]);
