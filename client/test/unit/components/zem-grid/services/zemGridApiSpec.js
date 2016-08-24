/* globals angular, jasmine, describe, it, beforeEach, expect, module, inject, spyOn */

describe('zemGridApi', function () {
    var $rootScope;
    var zemGridApi;
    var zemGridObject;
    var zemGridPubSub;

    beforeEach(module('one'));

    beforeEach(inject(function (_$rootScope_, _zemGridObject_, _zemGridApi_, _zemGridPubSub_) {
        $rootScope = _$rootScope_;
        zemGridObject = _zemGridObject_;
        zemGridApi = _zemGridApi_;
        zemGridPubSub = _zemGridPubSub_;
    }));

    function createGrid () {
        var grid = zemGridObject.createGrid();
        var scope = $rootScope.$new();

        grid.meta.scope = scope;
        grid.meta.pubsub = zemGridPubSub.createInstance(scope);
        grid.meta.data = {};
        grid.meta.dataService = {};
        grid.meta.selectionService = {};
        grid.meta.columnsService = {};
        grid.meta.notificationService = {};

        grid.header.columns.push(zemGridObject.createColumn({}));
        grid.header.columns.push(zemGridObject.createColumn({}));
        grid.header.columns.push(zemGridObject.createColumn({}));

        grid.footer.row = zemGridObject.createRow('', {}, 0, null);

        var baseRow = zemGridObject.createRow('', {}, 1, grid.footer.row);
        grid.body.rows.push(baseRow);
        grid.body.rows.push(zemGridObject.createRow('', {}, 2, baseRow));
        grid.body.rows.push(zemGridObject.createRow('', {}, 2, baseRow));

        return grid;
    }

    it('should provide high-level interface to grid object', function () {
        var grid = createGrid();
        var api = zemGridApi.createInstance(grid);

        expect(api.isInitialized()).toBe(grid.meta.initialized);
        expect(api.getMetaData()).toBe(grid.meta.data);
        expect(api.getRows().length).toBe(4); // body rows + footer
        expect(api.getColumns().length).toBe(3);
    });


    it('should register listeners to pubsub', function () {
        var grid = createGrid();
        spyOn(grid.meta.pubsub, 'register');

        var pubsub = grid.meta.pubsub;
        var api = zemGridApi.createInstance(grid);

        expect(grid.meta.pubsub.register).not.toHaveBeenCalled();

        var callback = function () {};
        api.onMetaDataUpdated(null, callback);
        expect(grid.meta.pubsub.register).toHaveBeenCalledWith(pubsub.EVENTS.METADATA_UPDATED, null, callback);

        api.onDataUpdated(null, callback);
        expect(grid.meta.pubsub.register).toHaveBeenCalledWith(pubsub.EVENTS.DATA_UPDATED, null, callback);

        api.onColumnsUpdated(null, callback);
        expect(grid.meta.pubsub.register).toHaveBeenCalledWith(pubsub.EVENTS.EXT_COLUMNS_UPDATED, null, callback);

        api.onSelectionUpdated(null, callback);
        expect(grid.meta.pubsub.register).toHaveBeenCalledWith(pubsub.EVENTS.EXT_SELECTION_UPDATED, null, callback);
    });
});
