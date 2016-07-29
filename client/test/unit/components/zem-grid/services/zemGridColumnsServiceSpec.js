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
        grid.meta.dataService = {
            getBreakdown: function () { return ['base_level', 'age']; }
        };

        grid.header.columns.push(zemGridObject.createColumn({}));
        grid.header.columns.push(zemGridObject.createColumn({}));
        grid.header.columns.push(zemGridObject.createColumn({}));

        return grid;
    }

    it('should persist changes to storage service', function () {
        spyOn(zemGridStorageService, 'loadColumns');
        spyOn(zemGridStorageService, 'saveColumns');

        var grid = createGrid();
        var pubsub = grid.meta.pubsub;

        var columnsService = zemGridColumnsService.createInstance(grid);
        pubsub.notify(pubsub.EVENTS.METADATA_UPDATED);
        expect(zemGridStorageService.loadColumns).toHaveBeenCalled();

        columnsService.setColumnVisibility(grid.header.columns[0], false);
        expect(zemGridStorageService.saveColumns).toHaveBeenCalled();
    });

    it('should allow setting column visibility', function () {
        var grid = createGrid();
        var columnsService = zemGridColumnsService.createInstance(grid);
        grid.meta.pubsub.notify(grid.meta.pubsub.EVENTS.METADATA_UPDATED);

        var columns = grid.header.columns;
        columnsService.setColumnVisibility(columns[0], false);
        expect(columnsService.isColumnVisible(columns[0])).toBe(false);
        expect(columnsService.isColumnVisible(columns[1])).toBe(true);
        expect(columnsService.isColumnVisible(columns[2])).toBe(true);
        expect(columnsService.getVisibleColumns().length).toBe(2);

        columnsService.setVisibleColumns(columns, false);
        expect(columnsService.isColumnVisible(columns[0])).toBe(false);
        expect(columnsService.isColumnVisible(columns[1])).toBe(false);
        expect(columnsService.isColumnVisible(columns[2])).toBe(false);
        expect(columnsService.getVisibleColumns().length).toBe(0);

        columnsService.setVisibleColumns(columns, true);
        expect(columnsService.getVisibleColumns().length).toBe(3);
    });

    it('should disable columns that cannot be viewed using current breakdown configuration', function () {
        var grid = createGrid();
        spyOn(grid.meta.dataService, 'getBreakdown');

        var pubsub = grid.meta.pubsub;
        zemGridColumnsService.createInstance(grid);

        var columns = grid.header.columns;
        columns[0].data.breakdowns = ['breakdown2', 'breakdown3'];
        columns[1].data.breakdowns = ['breakdown4'];
        columns[2].data.breakdowns = undefined;

        grid.meta.dataService.getBreakdown.and.returnValue([
            {query: 'breakdown1'},
            {query: 'breakdown2'},
            {query: 'breakdown5'}
        ]);

        pubsub.notify(pubsub.EVENTS.DATA_UPDATED);

        expect(columns[0].disabled).toBe(false);
        expect(columns[1].disabled).toBe(true);
        expect(columns[2].disabled).toBe(false);

        grid.meta.dataService.getBreakdown.and.returnValue([
            {query: 'breakdown4'},
        ]);

        pubsub.notify(pubsub.EVENTS.DATA_UPDATED);

        expect(columns[0].disabled).toBe(true);
        expect(columns[1].disabled).toBe(false);
        expect(columns[2].disabled).toBe(false);

    });

    it('should hide disabled columns', function () {
        var grid = createGrid();
        var columnsService = zemGridColumnsService.createInstance(grid);

        var columns = grid.header.columns;
        columns[0].disabled = true;
        expect(columnsService.getVisibleColumns().length).toBe(2);

        columns[0].disabled = false;
        expect(columnsService.getVisibleColumns().length).toBe(3);

        columns[0].disabled = undefined;
        expect(columnsService.getVisibleColumns().length).toBe(3);
    });
});
