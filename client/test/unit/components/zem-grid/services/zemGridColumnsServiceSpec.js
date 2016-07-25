/* globals angular, jasmine, describe, it, beforeEach, expect, module, inject, spyOn */

describe('zemGridColumnsService', function () {
    var $rootScope;
    var zemGridObject;
    var zemGridPubSub;
    var zemGridColumnsService;
    var zemGridStorageService;

    beforeEach(module('one'));

    beforeEach(module(function ($provide) {
        $provide.value('zemGridStorageService', {saveColumns: angular.noop, loadColumns: angular.noop});
        $provide.value('zemGridUIService', {resizeGridColumns: angular.noop});
    }));

    beforeEach(inject(function (_$rootScope_, _zemGridObject_, _zemGridPubSub_, _zemGridColumnsService_, _zemGridStorageService_) {
        $rootScope = _$rootScope_;
        zemGridObject = _zemGridObject_;
        zemGridPubSub = _zemGridPubSub_;
        zemGridColumnsService = _zemGridColumnsService_;
        zemGridStorageService = _zemGridStorageService_;
    }));

    function createGrid () {
        var grid = zemGridObject.createGrid();
        var scope = $rootScope.$new();

        grid.meta.scope = scope;
        grid.meta.pubsub = zemGridPubSub.createInstance(scope);
        grid.meta.options = {};
        grid.meta.data = {};

        grid.header.columns.push(zemGridObject.createColumn({}));
        grid.header.columns.push(zemGridObject.createColumn({}));
        grid.header.columns.push(zemGridObject.createColumn({}));

        return grid;
    }

    it('should persist changes to storage service', function () {
        spyOn (zemGridStorageService, 'loadColumns');
        spyOn (zemGridStorageService, 'saveColumns');

        var grid = createGrid();
        var pubsub = grid.meta.pubsub;

        var columnsService = zemGridColumnsService.createInstance(grid);
        pubsub.notify(pubsub.EVENTS.METADATA_UPDATED);
        expect(zemGridStorageService.loadColumns).toHaveBeenCalled();

        columnsService.setColumnVisibility (grid.header.columns[0], false);
        expect(zemGridStorageService.saveColumns).toHaveBeenCalled();
    });

    it('should allow setting column visibility', function () {
        var grid = createGrid();
        var columnsService = zemGridColumnsService.createInstance(grid);
        grid.meta.pubsub.notify(grid.meta.pubsub.EVENTS.METADATA_UPDATED);

        var columns = grid.header.columns;
        columnsService.setColumnVisibility(columns[0], false);
        expect (columnsService.isColumnVisible(columns[0])).toBe(false);
        expect (columnsService.isColumnVisible(columns[1])).toBe(true);
        expect (columnsService.isColumnVisible(columns[2])).toBe(true);
        expect (columnsService.getVisibleColumns().length).toBe(2);

        columnsService.setVisibleColumns(columns, false);
        expect (columnsService.isColumnVisible(columns[0])).toBe(false);
        expect (columnsService.isColumnVisible(columns[1])).toBe(false);
        expect (columnsService.isColumnVisible(columns[2])).toBe(false);
        expect (columnsService.getVisibleColumns().length).toBe(0);

        columnsService.setVisibleColumns(columns, true);
        expect (columnsService.getVisibleColumns().length).toBe(3);
    });
});
