describe('zemGridCollapseService', function() {
    var $rootScope;
    var zemGridObject;
    var zemGridPubSub;
    var zemGridCollapseService;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(angular.mock.module('one.mocks.NgZone'));

    beforeEach(inject(function(
        _$rootScope_,
        _zemGridObject_,
        _zemGridPubSub_,
        _zemGridCollapseService_
    ) {
        $rootScope = _$rootScope_;
        zemGridObject = _zemGridObject_;
        zemGridPubSub = _zemGridPubSub_;
        zemGridCollapseService = _zemGridCollapseService_;
    }));

    function createGrid() {
        var grid = zemGridObject.createGrid();
        var scope = $rootScope.$new();

        grid.meta.scope = scope;
        grid.meta.pubsub = zemGridPubSub.createInstance(scope);
        grid.meta.data = {};
        grid.meta.dataService = {
            getBreakdownLevel: function() {
                return 2;
            },
        };

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

    function countVisibleRows(grid) {
        var count = grid.body.rows.filter(function(row) {
            return row.visible;
        }).length;
        if (grid.footer.row && grid.footer.row.visible) count++;
        return count;
    }

    it('should collapse only rows that are not on last level and not footer', function() {
        var grid = createGrid();
        var collapseService = zemGridCollapseService.createInstance(grid);
        var rows = grid.body.rows;

        expect(collapseService.isRowCollapsable(rows[0])).toBe(true);
        expect(collapseService.isRowCollapsable(rows[1])).toBe(false);
        expect(collapseService.isRowCollapsable(rows[3])).toBe(true);
        expect(collapseService.isRowCollapsable(rows[4])).toBe(false);
        expect(collapseService.isRowCollapsable(grid.footer.row)).toBe(false);
    });

    it('should allow collapsing desired row', function() {
        var grid = createGrid();
        var collapseService = zemGridCollapseService.createInstance(grid);
        var rows = grid.body.rows;

        expect(countVisibleRows(grid)).toBe(7);

        // Collapse both base level rows
        // Expected visible rows - footer + 2 base level rows
        collapseService.setRowCollapsed(rows[0], true);
        collapseService.setRowCollapsed(rows[3], true);
        expect(collapseService.isRowCollapsed(rows[0])).toBe(true);
        expect(collapseService.isRowCollapsed(rows[3])).toBe(true);
        expect(countVisibleRows(grid)).toBe(3);

        // Un-Collapse one base level row
        // Expected visible rows - footer row + 2 base level rows + 2 2nd level rows
        collapseService.setRowCollapsed(rows[0], false);
        expect(collapseService.isRowCollapsed(rows[0])).toBe(false);
        expect(countVisibleRows(grid)).toBe(5);
    });

    it('should allow collapsing all rows of desired level', function() {
        var grid = createGrid();
        var collapseService = zemGridCollapseService.createInstance(grid);
        var rows = grid.body.rows;

        // Collapse base level rows
        // Expected visible rows - footer + 2 base level rows
        collapseService.setLevelCollapsed(1, true);
        expect(countVisibleRows(grid)).toBe(3);

        // Un-Collapse one base level row
        // Expected visible rows - footer row + 2 base level rows + 2 2nd level rows
        collapseService.setRowCollapsed(rows[0], false);
        expect(countVisibleRows(grid)).toBe(5);
    });

    it('should notify listeners about the updates', function() {
        var grid = createGrid();
        var collapseService = zemGridCollapseService.createInstance(grid);

        var dataUpdatedSpy = jasmine.createSpy();
        var collapseUpdatedSpy = jasmine.createSpy();

        grid.meta.pubsub.register(
            grid.meta.pubsub.EVENTS.DATA_UPDATED,
            null,
            dataUpdatedSpy
        );
        grid.meta.pubsub.register(
            grid.meta.pubsub.EVENTS.EXT_COLLAPSE_UPDATED,
            null,
            collapseUpdatedSpy
        );

        collapseService.setRowCollapsed(grid.body.rows[0], true);
        expect(dataUpdatedSpy).toHaveBeenCalled();
        expect(collapseUpdatedSpy).toHaveBeenCalled();
        dataUpdatedSpy.calls.reset();
        collapseUpdatedSpy.calls.reset();

        collapseService.setLevelCollapsed(1, true);
        expect(dataUpdatedSpy).toHaveBeenCalled();
        expect(collapseUpdatedSpy).toHaveBeenCalled();
    });
});
