angular.module('one.widgets').factory('zemGridObject', function (zemGridConstants) {

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
            options: null,      // Options (enableSelection, maxSelectedRows, etc.)
            service: null,      // zemGridDataService - access to data
            pubsub: null,       // zemGridPubSub - internal message queue
            data: null,         // meta-data retrieved through Endpoint - columns definitions
            scope: null,        // zem-grid scope used for running $digest and $emit internally
        };

        this.ui = {
            element: null,      // zem-grid dom element
            columnsWidths: [],  // columns widths used by grid cells
        };

        this.ext = {            // extension objects (placeholder)
            selection: null,    // selection extensions
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
        var id = createRowId(type, data, level);
        return {
            id: id,              // Row id
            type: type,          // Type of a row (STATS, BREAKDOWN)
            entity: data.entity, // Which entity's stats does row display (account, campaign, ad_group, content_ad)
            data: data,          // Data that corresponds to this row (stats or breakdown object - see DataSource)
            level: level,        // Level of data in breakdown tree which this row represents
            parent: parent,      // Parent row - row on which breakdown has been made
            collapsed: false,    // Collapse flag used by collapsing feature
            visible: true,       // Visibility flag - row can be hidden for different reasons (e.g. collapsed parent)
        };
    }

    function createColumn (data) {
        return {
            type: data.type,    // Reuse data type - type of column (text, link, icon, etc.)
            field: data.field,  // Reuse data field - some kind of id  (data retrieval, storage, etc.)
            data: data,         // Column meta-data retrieved from endpoint
            visible: true,      // Visibility flag
        };
    }

    function createRowId (type, data, level) {
        if (type === zemGridConstants.gridRowType.STATS) {
            if (level === zemGridConstants.gridRowLevel.FOOTER) return 'id-level0';
            return data.breakdownId;
        }

        if (type === zemGridConstants.gridRowType.BREAKDOWN) {
            if (level === zemGridConstants.gridRowLevel.FOOTER) return 'breakdown-id-level0';
            return 'breakdown-' + data.breakdownId;
        }
    }


    return {
        createGrid: createGrid,
        createRow: createRow,
        createColumn: createColumn,
    };
});
