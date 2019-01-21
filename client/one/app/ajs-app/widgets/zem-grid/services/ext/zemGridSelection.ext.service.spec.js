describe('zemGridSelectionService', function() {
    var $rootScope;
    var zemGridConstants;
    var zemGridObject;
    var zemGridPubSub;
    var zemGridSelectionService;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(angular.mock.module('one.mocks.NgZone'));

    beforeEach(inject(function(
        _$rootScope_,
        _zemGridConstants_,
        _zemGridObject_,
        _zemGridPubSub_,
        _zemGridSelectionService_
    ) {
        // eslint-disable-line max-len
        $rootScope = _$rootScope_;
        zemGridConstants = _zemGridConstants_;
        zemGridObject = _zemGridObject_;
        zemGridPubSub = _zemGridPubSub_;
        zemGridSelectionService = _zemGridSelectionService_;
    }));

    function createGrid() {
        var grid = zemGridObject.createGrid();
        var scope = $rootScope.$new();

        grid.meta.scope = scope;
        grid.meta.pubsub = zemGridPubSub.createInstance(scope);
        grid.meta.data = {};
        grid.meta.options = {};
        grid.meta.options.selection = {
            enabled: true,
            filtersEnabled: true,
            levels: [0, 1],
            customFilters: [],
        };

        grid.header.columns.push(zemGridObject.createColumn({}));
        grid.header.columns.push(zemGridObject.createColumn({}));
        grid.header.columns.push(zemGridObject.createColumn({}));

        grid.footer.row = zemGridObject.createRow(
            zemGridConstants.gridRowType.STATS,
            {},
            0,
            null
        );

        var baseRow = zemGridObject.createRow(
            zemGridConstants.gridRowType.STATS,
            {breakdownId: 'id-1-1'},
            1,
            grid.footer.row
        ); // eslint-disable-line max-len
        grid.body.rows.push(baseRow);
        grid.body.rows.push(
            zemGridObject.createRow(
                zemGridConstants.gridRowType.STATS,
                {breakdownId: 'id-2-1'},
                2,
                baseRow
            )
        ); // eslint-disable-line max-len
        grid.body.rows.push(
            zemGridObject.createRow(
                zemGridConstants.gridRowType.STATS,
                {breakdownId: 'id-2-2'},
                2,
                baseRow
            )
        ); // eslint-disable-line max-len

        return grid;
    }

    it('should initialize properly (pubsub registration and selection initialization)', function() {
        var grid = createGrid();
        var pubsub = grid.meta.pubsub;
        spyOn(grid.meta.pubsub, 'register').and.callThrough();
        spyOn(grid.meta.pubsub, 'notify').and.callThrough();

        var selectionService = zemGridSelectionService.createInstance(grid);

        expect(grid.meta.pubsub.register).toHaveBeenCalledWith(
            pubsub.EVENTS.DATA_UPDATED,
            null,
            jasmine.any(Function)
        );
        expect(grid.meta.pubsub.notify).toHaveBeenCalledWith(
            pubsub.EVENTS.EXT_SELECTION_UPDATED,
            jasmine.any(Object)
        );

        expect(selectionService.getSelection()).toEqual({
            type: zemGridConstants.gridSelectionFilterType.NONE,
            filter: jasmine.any(Object),
            selected: [],
            unselected: [],
        });
    });

    it('should notify changes', function() {
        var grid = createGrid();
        var pubsub = grid.meta.pubsub;
        spyOn(grid.meta.pubsub, 'notify').and.callThrough();

        var selectionService = zemGridSelectionService.createInstance(grid);
        selectionService.setFilter(
            zemGridConstants.gridSelectionFilterType.ALL
        );
        selectionService.setRowSelection(grid.body.rows[0], false);

        expect(grid.meta.pubsub.notify.calls.count()).toBe(3);
        expect(grid.meta.pubsub.notify.calls.allArgs()).toEqual([
            [pubsub.EVENTS.EXT_SELECTION_UPDATED, jasmine.any(Object)],
            [pubsub.EVENTS.EXT_SELECTION_UPDATED, jasmine.any(Object)],
            [pubsub.EVENTS.EXT_SELECTION_UPDATED, jasmine.any(Object)],
        ]);
    });

    it('should allow selection based on allowed levels configuration', function() {
        var grid = createGrid();
        var selectionService = zemGridSelectionService.createInstance(grid);
        var config = {
            enabled: true,
            filtersEnabled: true,
            levels: [0, 1],
            customFilters: [{}, {}],
        };

        selectionService.setConfig(config);
        expect(selectionService.isSelectionEnabled()).toBe(true);
        expect(selectionService.isFilterSelectionEnabled()).toBe(true);
        expect(selectionService.isRowSelectionEnabled(grid.body.rows[0])).toBe(
            true
        );
        expect(selectionService.isRowSelectionEnabled(grid.body.rows[1])).toBe(
            false
        );
        expect(selectionService.isRowSelectionEnabled(grid.footer.row)).toBe(
            true
        );
        expect(selectionService.getCustomFilters()).toBe(config.customFilters);

        config.enabled = false;
        selectionService.setConfig(config);
        expect(selectionService.isSelectionEnabled()).toBe(false);

        config.enabled = true;
        config.filtersEnabled = false;
        expect(selectionService.isSelectionEnabled()).toBe(true);
        expect(selectionService.isFilterSelectionEnabled()).toBe(false);

        config.levels = [2];
        expect(selectionService.isRowSelectionEnabled(grid.body.rows[0])).toBe(
            false
        );
        expect(selectionService.isRowSelectionEnabled(grid.body.rows[1])).toBe(
            true
        );
        expect(selectionService.isRowSelectionEnabled(grid.footer.row)).toBe(
            false
        );
    });

    it('should correctly persist selections using NONE filter', function() {
        var grid = createGrid();
        var selectionService = zemGridSelectionService.createInstance(grid);

        selectionService.setFilter(
            zemGridConstants.gridSelectionFilterType.NONE
        );
        expect(selectionService.isRowSelected(grid.body.rows[0])).toBe(false);
        expect(selectionService.isRowSelected(grid.footer.row)).toBe(false);
        expect(selectionService.getSelection().selected.length).toBe(0);
        expect(selectionService.getSelection().unselected.length).toBe(0);

        selectionService.setRowSelection(grid.body.rows[0], true);
        expect(selectionService.isRowSelected(grid.body.rows[0])).toBe(true);
        expect(selectionService.isRowSelected(grid.footer.row)).toBe(false);
        expect(selectionService.getSelection().selected.length).toBe(1);
        expect(selectionService.getSelection().unselected.length).toBe(0);
    });

    it('should correctly persist selections using ALL filter', function() {
        var grid = createGrid();
        var selectionService = zemGridSelectionService.createInstance(grid);

        selectionService.setFilter(
            zemGridConstants.gridSelectionFilterType.ALL
        );
        expect(selectionService.isRowSelected(grid.body.rows[0])).toBe(true);
        expect(selectionService.isRowSelected(grid.footer.row)).toBe(true);
        expect(selectionService.getSelection().selected.length).toBe(0);
        expect(selectionService.getSelection().unselected.length).toBe(0);

        selectionService.setRowSelection(grid.body.rows[0], false);
        expect(selectionService.isRowSelected(grid.body.rows[0])).toBe(false);
        expect(selectionService.isRowSelected(grid.footer.row)).toBe(true);
        expect(selectionService.getSelection().selected.length).toBe(0);
        expect(selectionService.getSelection().unselected.length).toBe(1);
    });

    it('should correctly persist selections using CUSTOM filter', function() {
        var grid = createGrid();
        var selectionService = zemGridSelectionService.createInstance(grid);

        selectionService.setFilter(
            zemGridConstants.gridSelectionFilterType.CUSTOM,
            {
                callback: function(row) {
                    return row.level === 1;
                },
            }
        );

        expect(selectionService.isRowSelected(grid.body.rows[0])).toBe(true);
        expect(selectionService.isRowSelected(grid.footer.row)).toBe(false);
        expect(selectionService.getSelection().selected.length).toBe(0);
        expect(selectionService.getSelection().unselected.length).toBe(0);

        selectionService.setRowSelection(grid.body.rows[0], false);
        selectionService.setRowSelection(grid.footer.row, true);
        expect(selectionService.isRowSelected(grid.body.rows[0])).toBe(false);
        expect(selectionService.isRowSelected(grid.footer.row)).toBe(true);
        expect(selectionService.getSelection().selected.length).toBe(1);
        expect(selectionService.getSelection().unselected.length).toBe(1);
    });

    it('should be able to clear selection', function() {
        var grid = createGrid();
        var selectionService = zemGridSelectionService.createInstance(grid);

        selectionService.setRowSelection(grid.body.rows[0], true);
        selectionService.setRowSelection(grid.footer.row, true);
        expect(selectionService.getSelection().selected.length).toBe(2);

        selectionService.clearSelection();
        expect(selectionService.getSelection().selected.length).toBe(0);
    });

    it('should preserve selection between dataup dates', function() {
        var grid = createGrid();
        var selectionService = zemGridSelectionService.createInstance(grid);

        selectionService.setRowSelection(grid.body.rows[0], true);
        selectionService.setRowSelection(grid.footer.row, true);
        expect(selectionService.getSelection().selected.length).toBe(2);

        selectionService.clearSelection();
        expect(selectionService.getSelection().selected.length).toBe(0);
    });

    it('should preserve selection between data updates', function() {
        var grid = createGrid();
        var pubsub = grid.meta.pubsub;

        var selectionService = zemGridSelectionService.createInstance(grid);
        selectionService.setRowSelection(grid.body.rows[0], true);
        selectionService.setRowSelection(grid.body.rows[2], true);
        selectionService.setRowSelection(grid.footer.row, true);

        grid.body.rows = [];
        pubsub.notify(pubsub.EVENTS.DATA_UPDATED);
        expect(selectionService.getSelection().selected.length).toBe(3);

        grid.body = createGrid().body;
        pubsub.notify(pubsub.EVENTS.DATA_UPDATED);
        expect(selectionService.getSelection().selected.length).toBe(3);

        grid.body = createGrid().body;
        grid.body.rows = grid.body.rows.slice(0, 2);
        pubsub.notify(pubsub.EVENTS.DATA_UPDATED);
        expect(selectionService.getSelection().selected.length).toBe(2);
    });
});
