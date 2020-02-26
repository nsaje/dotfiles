describe('zemSelectionService', function() {
    var zemSelectionService;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function(_zemSelectionService_) {
        zemSelectionService = _zemSelectionService_;
    }));

    it('isTotalsSelected should return false if totals are not selected', function() {
        expect(zemSelectionService.isTotalsSelected()).toBe(true);
    });

    it('isTotalsSelected should return true if totals are selected', function() {
        zemSelectionService.init();
        expect(zemSelectionService.isTotalsSelected()).toBe(true);
        zemSelectionService.unselectTotals();
        expect(zemSelectionService.isTotalsSelected()).toBe(false);
        zemSelectionService.selectTotals();
        expect(zemSelectionService.isTotalsSelected()).toBe(true);
    });

    it('isAllSelected should return false if all is not selected', function() {
        expect(zemSelectionService.isAllSelected()).toBe(false);
    });

    it('isTotalsSelected should return true if all is selected', function() {
        zemSelectionService.init();
        expect(zemSelectionService.isAllSelected()).toBe(false);
        zemSelectionService.selectAll();
        expect(zemSelectionService.isAllSelected()).toBe(true);
        zemSelectionService.unselectAll();
        expect(zemSelectionService.isAllSelected()).toBe(false);
    });

    it('should correctly set selection', function() {
        zemSelectionService.setSelection({
            selected: [1, 3],
            unselected: [2],
            totalsUnselected: false,
        });
        expect(zemSelectionService.getSelection()).toEqual({
            selected: ['1', '3'],
            unselected: ['2'],
            totalsUnselected: false,
            all: false,
            batch: null,
        });
    });

    it('should correctly remove number id', function() {
        zemSelectionService.init();
        zemSelectionService.setSelection({
            selected: [1, 2, 3],
            unselected: [],
            totalsUnselected: false,
        });
        zemSelectionService.remove(2);
        expect(zemSelectionService.getSelection().selected).toEqual(['1', '3']);
    });

    it('should correctly remove string id', function() {
        zemSelectionService.init();
        zemSelectionService.setSelection({
            selected: [1, 2, 3],
            unselected: [],
            totalsUnselected: false,
        });
        zemSelectionService.remove('2');
        expect(zemSelectionService.getSelection().selected).toEqual(['1', '3']);
    });

    it('should correctly remove array of ids', function() {
        zemSelectionService.init();
        zemSelectionService.setSelection({
            selected: [1, 2, 3],
            unselected: [],
            totalsUnselected: false,
        });
        zemSelectionService.remove([2, '3']);
        expect(zemSelectionService.getSelection().selected).toEqual(['1']);
    });

    it('should add id to unselected when removing it and all is selected', function() {
        zemSelectionService.init();
        zemSelectionService.setSelection({
            selected: [1, 2, 3],
            all: true,
        });
        zemSelectionService.remove(3);
        expect(zemSelectionService.getSelection().selected).toEqual(['1', '2']);
        expect(zemSelectionService.getSelection().unselected).toEqual(['3']);
    });

    it('should add id to unselected when removing it and batch is selected', function() {
        zemSelectionService.init();
        zemSelectionService.setSelection({
            selected: [1, 2, 3],
            batch: 999,
        });
        zemSelectionService.remove(3);
        expect(zemSelectionService.getSelection().selected).toEqual(['1', '2']);
        expect(zemSelectionService.getSelection().unselected).toEqual(['3']);
        expect(zemSelectionService.getSelection().batch).toEqual(999);
    });

    it('should correctly select totals', function() {
        zemSelectionService.init();
        zemSelectionService.setSelection({
            selected: [1, 2, 3],
        });
        zemSelectionService.selectTotals();
        expect(zemSelectionService.getSelection().selected).toEqual([
            '1',
            '2',
            '3',
        ]);
        expect(zemSelectionService.isTotalsSelected()).toBe(true);
    });

    it('should correctly unselect totals', function() {
        zemSelectionService.init();
        zemSelectionService.setSelection({
            selected: [1, 2, 3],
        });
        zemSelectionService.unselectTotals();
        expect(zemSelectionService.getSelection().selected).toEqual([
            '1',
            '2',
            '3',
        ]);
        expect(zemSelectionService.isTotalsSelected()).toBe(false);
    });

    it('should correctly select all', function() {
        zemSelectionService.init();
        zemSelectionService.setSelection({
            selected: [1, 2, 3],
        });
        zemSelectionService.selectAll();
        expect(zemSelectionService.getSelection().selected).toEqual([]);
        expect(zemSelectionService.isTotalsSelected()).toBe(true);
        expect(zemSelectionService.isAllSelected()).toBe(true);
    });
});
