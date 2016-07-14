/* globals angular, jasmine, describe, it, beforeEach, expect, module, inject, spyOn */

describe('zemGridApi', function () {
    var $rootScope;
    var zemGridApi;
    var zemGridObject;
    var zemGridPubSub;
    var zemGridStorageService;

    beforeEach(module('one'));

    beforeEach(module(function ($provide) {
        $provide.value('zemGridStorageService', {saveColumns: angular.noop, loadColumns: angular.noop});
    }));

    beforeEach(inject(function (_$rootScope_, _zemGridObject_, _zemGridApi_, _zemGridPubSub_, _zemGridStorageService_) {
        $rootScope = _$rootScope_;
        zemGridObject = _zemGridObject_;
        zemGridApi = _zemGridApi_;
        zemGridPubSub = _zemGridPubSub_;
        zemGridStorageService = _zemGridStorageService_;
    }));

    function createGrid () {
        var grid = zemGridObject.createGrid();
        var scope = $rootScope.$new();

        grid.meta.scope = scope;
        grid.meta.pubsub = zemGridPubSub.createInstance(scope);
        grid.meta.data = {};
        grid.meta.service = {};

        grid.header.columns.push(zemGridObject.createColumn({}));
        grid.header.columns.push(zemGridObject.createColumn({}));
        grid.header.columns.push(zemGridObject.createColumn({}));

        grid.footer.row = zemGridObject.createRow('', {}, 0, null);

        var baseRow1 = zemGridObject.createRow('', {}, 1, grid.footer.row);
        grid.body.rows.push(baseRow1);
        grid.body.rows.push(zemGridObject.createRow('', {}, 2, baseRow1));
        grid.body.rows.push(zemGridObject.createRow('', {}, 2, baseRow1));

        var baseRow2 = zemGridObject.createRow('', {}, 1, grid.footer.row);
        grid.body.rows.push(baseRow2);
        grid.body.rows.push(zemGridObject.createRow('', {}, 2, baseRow2));
        grid.body.rows.push(zemGridObject.createRow('', {}, 2, baseRow2));

        return grid;
    }

    it('should provide high-level interface to grid object', function () {
        var grid = createGrid();
        var api = zemGridApi.createInstance(grid);

        expect(api.getMetaData()).toBe(grid.meta.data);
        expect(api.getDataService()).toBe(grid.meta.service);
        expect(api.getRows().length).toBe(7); // body rows + footer
        expect(api.getColumns().length).toBe(3);
    });

    it('should allow selecting rows', function () {
        var grid = createGrid();
        var api = zemGridApi.createInstance(grid);
        var rows = api.getRows();

        expect(api.getSelectedRows().length).toBe(0);

        api.setSelectedRows(rows.slice(0, 2), true);
        expect(api.getSelectedRows().length).toBe(2);

        api.setSelectedRows(rows.slice(0, 1), false);
        expect(api.getSelectedRows().length).toBe(1);
    });

    it('should allow setting visibility on columns', function () {
        var grid = createGrid();
        var api = zemGridApi.createInstance(grid);
        var columns = api.getColumns();

        expect(api.getVisibleColumns().length).toBe(3);

        api.setVisibleColumns(columns.slice(0, 2), false);
        expect(api.getVisibleColumns().length).toBe(1);

        api.setVisibleColumns(columns.slice(0, 1), true);
        expect(api.getVisibleColumns().length).toBe(2);
    });

    it('should save column settings', function () {
        spyOn(zemGridStorageService, 'saveColumns');
        var grid = createGrid();
        var api = zemGridApi.createInstance(grid);

        expect(api.getVisibleColumns().length).toBe(3);
        expect(zemGridStorageService.saveColumns).not.toHaveBeenCalled();
        api.setVisibleColumns(api.getColumns().slice(0, 2), false);
        expect(zemGridStorageService.saveColumns).toHaveBeenCalled();
    });

    it('should allow collapsing desired row', function () {
        var grid = createGrid();
        var api = zemGridApi.createInstance(grid);
        var rows = api.getRows();

        expect(api.getVisibleRows().length).toBe(7);

        // Collapse both base level rows
        // Expected visible rows - footer + 2 base level rows
        api.setCollapsedRows([rows[0], rows[3]], true);
        expect(api.getVisibleRows().length).toBe(3);

        // Un-Collapse one base level row
        // Expected visible rows - footer row + 2 base level rows + 2 2nd level rows
        api.setCollapsedRows(rows[0], false);
        expect(api.getVisibleRows().length).toBe(5);
    });

    it('should allow collapsing all rows of desired level', function () {
        var grid = createGrid();
        var api = zemGridApi.createInstance(grid);
        var rows = api.getRows();

        // Collapse base level rows
        // Expected visible rows - footer + 2 base level rows
        api.setCollapsedLevel(1, true);
        expect(api.getVisibleRows().length).toBe(3);

        // Un-Collapse one base level row
        // Expected visible rows - footer row + 2 base level rows + 2 2nd level rows
        api.setCollapsedRows(rows[0], false);
        expect(api.getVisibleRows().length).toBe(5);
    });

    it('should register to relevant pubsub events on initialization', function () {
        var grid = createGrid();
        spyOn(grid.meta.pubsub, 'register');
        zemGridApi.createInstance(grid);
        expect(grid.meta.pubsub.register).toHaveBeenCalled();
    });

    it('should notify listeners about the changes', function () {
        var grid = createGrid();
        var api = zemGridApi.createInstance(grid);
        var columns = api.getColumns();
        var rows = api.getRows();


        var selectionSpy = jasmine.createSpy();
        api.onRowsSelectionChanged(null, selectionSpy);
        api.setSelectedRows(rows[0], false);
        expect(selectionSpy).toHaveBeenCalledWith(jasmine.any(Object), [rows[0]]);

        var collapseSpy = jasmine.createSpy();
        api.onRowsCollapseChanged(null, collapseSpy);
        api.setCollapsedRows(rows[0], true);
        expect(collapseSpy).toHaveBeenCalledWith(jasmine.any(Object), [rows[0]]);

        var columnsVisibilitySpy = jasmine.createSpy();
        api.onColumnsVisibilityChanged(null, columnsVisibilitySpy);
        api.setVisibleColumns(columns[0], false);
        expect(columnsVisibilitySpy).toHaveBeenCalledWith(jasmine.any(Object), [columns[0]]);
    });
});
