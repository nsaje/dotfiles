describe('zemGridObject', function() {
    var zemGridObject;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function(_zemGridObject_) {
        zemGridObject = _zemGridObject_;
    }));

    it('should create default grid object', function() {
        var grid = zemGridObject.createGrid();

        expect(grid).toBeDefined();
        expect(grid.header).toBeDefined();
        expect(grid.body).toBeDefined();
        expect(grid.footer).toBeDefined();
        expect(grid.meta).toBeDefined();
        expect(grid.ui).toBeDefined();

        expect(grid.header.columns).toEqual([]);
        expect(grid.body.rows).toEqual([]);
        expect(grid.footer.row).toEqual(null);
    });

    it('should create default row object', function() {
        var type = 'stats';
        var data = {};
        var level = 1;
        var parent = {};
        var row = zemGridObject.createRow(type, data, level, parent);

        expect(row.type).toBe(type);
        expect(row.data).toBe(data);
        expect(row.level).toBe(level);
        expect(row.parent).toBe(parent);
        expect(row.visible).toBe(true);
        expect(row.collapsed).toBe(false);
    });

    it('should create default column object', function() {
        var data = {
            type: 'currency',
            field: 'cost',
        };
        var column = zemGridObject.createColumn(data);

        expect(column.type).toBe(data.type);
        expect(column.field).toBe(data.field);
        expect(JSON.stringify(column.data)).toBe(JSON.stringify(data));
        expect(column.visible).toBe(true);
    });
});
