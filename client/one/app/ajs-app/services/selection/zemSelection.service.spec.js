describe('zemSelectionService', function() {
    var $location;
    var zemSelectionService;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function(_$location_, _zemSelectionService_) {
        $location = _$location_;
        zemSelectionService = _zemSelectionService_;
    }));

    it('should init correctly without URL params', function() {
        zemSelectionService.init();
        expect(zemSelectionService.getSelection()).toEqual({
            selected: [],
            unselected: [],
            totalsUnselected: false,
            all: false,
            batch: null,
        });
    });

    it('should init correctly with URL params', function() {
        spyOn($location, 'search').and.returnValue({
            selected_ids: '1,2,3,whatever,',
            unselected_ids: '4,5,6,:)',
            selected_totals: true,
            selected_all: true,
            selected_batch_id: '999',
        });
        zemSelectionService.init();
        expect(zemSelectionService.getSelection()).toEqual({
            selected: [1, 2, 3],
            unselected: [4, 5, 6],
            totalsUnselected: false,
            all: true,
            batch: 999,
        });
    });

    it('should correctly determine if an id is in selected list', function() {
        spyOn($location, 'search').and.returnValue({
            selected_ids: '1',
        });
        zemSelectionService.init();
        expect(zemSelectionService.isIdInSelected(1)).toBe(true);
        expect(zemSelectionService.isIdInSelected(2)).toBe(false);
    });

    it('should correctly determine if an id is in unselected list', function() {
        spyOn($location, 'search').and.returnValue({
            unselected_ids: '1',
        });
        zemSelectionService.init();
        expect(zemSelectionService.isIdInUnselected(1)).toBe(true);
        expect(zemSelectionService.isIdInUnselected(2)).toBe(false);
    });

    it('isTotalsSelected should return false if totals are not selected', function() {
        expect(zemSelectionService.isTotalsSelected(2)).toBe(true);
    });

    it('isTotalsSelected should return true if totals are selected', function() {
        spyOn($location, 'search').and.returnValue({
            totals_unselected: true,
        });
        zemSelectionService.init();
        expect(zemSelectionService.isTotalsSelected(2)).toBe(false);
    });

    it('isAllSelected should return false if all is not selected', function() {
        expect(zemSelectionService.isAllSelected()).toBe(false);
    });

    it('isTotalsSelected should return true if all is selected', function() {
        spyOn($location, 'search').and.returnValue({
            selected_all: true,
        });
        zemSelectionService.init();
        expect(zemSelectionService.isAllSelected(2)).toBe(true);
    });

    it('getSelectedBatch should return batch id if batch is selected', function() {
        spyOn($location, 'search').and.returnValue({
            selected_batch_id: 999,
        });
        zemSelectionService.init();
        expect(zemSelectionService.getSelectedBatch(2)).toEqual(999);
    });

    it('should correctly set selection', function() {
        zemSelectionService.setSelection({
            selected: [1, 3],
            unselected: [2],
            totalsUnselected: false,
        });
        expect(zemSelectionService.getSelection()).toEqual({
            selected: [1, 3],
            unselected: [2],
            totalsUnselected: false,
            all: false,
            batch: null,
        });
        expect($location.search()).toEqual({
            selected_ids: '1,3',
            unselected_ids: '2',
        });
    });

    it('should correctly remove number id', function() {
        var locationSpy = spyOn($location, 'search').and.returnValue({
            selected_ids: '1,2,3',
        });
        zemSelectionService.init();
        locationSpy.and.callThrough();
        zemSelectionService.remove(2);
        expect(zemSelectionService.getSelection().selected).toEqual([1, 3]);
        expect($location.search()).toEqual({
            selected_ids: '1,3',
        });
    });

    it('should correctly remove string id', function() {
        var locationSpy = spyOn($location, 'search').and.returnValue({
            selected_ids: '1,2,3',
        });
        zemSelectionService.init();
        locationSpy.and.callThrough();
        zemSelectionService.remove('3');
        expect(zemSelectionService.getSelection().selected).toEqual([1, 2]);
        expect($location.search()).toEqual({
            selected_ids: '1,2',
        });
    });

    it('should correctly remove array of ids', function() {
        var locationSpy = spyOn($location, 'search').and.returnValue({
            selected_ids: '1,2,3',
        });
        zemSelectionService.init();
        locationSpy.and.callThrough();
        zemSelectionService.remove([2, '3']);
        expect(zemSelectionService.getSelection().selected).toEqual([1]);
        expect($location.search()).toEqual({
            selected_ids: '1',
        });
    });

    it('should add id to unselected when removing it and all is selected', function() {
        var locationSpy = spyOn($location, 'search').and.returnValue({
            selected_ids: '1,2,3',
            selected_all: true,
        });
        zemSelectionService.init();
        locationSpy.and.callThrough();
        zemSelectionService.remove(3);
        expect(zemSelectionService.getSelection().selected).toEqual([1, 2]);
        expect(zemSelectionService.getSelection().unselected).toEqual([3]);
        expect($location.search()).toEqual({
            selected_ids: '1,2',
            unselected_ids: '3',
            selected_all: true,
        });
    });

    it('should add id to unselected when removing it and batch is selected', function() {
        var locationSpy = spyOn($location, 'search').and.returnValue({
            selected_ids: '1,2,3',
            selected_batch_id: 999,
        });
        zemSelectionService.init();
        locationSpy.and.callThrough();
        zemSelectionService.remove(3);
        expect(zemSelectionService.getSelection().selected).toEqual([1, 2]);
        expect(zemSelectionService.getSelection().unselected).toEqual([3]);
        expect($location.search()).toEqual({
            selected_ids: '1,2',
            unselected_ids: '3',
            selected_batch_id: 999,
        });
    });

    it('should correctly select totals', function() {
        var locationSpy = spyOn($location, 'search').and.returnValue({
            selected_ids: '1,2,3',
        });
        zemSelectionService.init();
        locationSpy.and.callThrough();
        zemSelectionService.selectTotals();
        expect(zemSelectionService.getSelection().selected).toEqual([1, 2, 3]);
        expect(zemSelectionService.isTotalsSelected()).toBe(true);
        expect($location.search()).toEqual({
            selected_ids: '1,2,3',
        });
    });

    it('should correctly unselect totals', function() {
        var locationSpy = spyOn($location, 'search').and.returnValue({
            selected_ids: '1,2,3',
        });
        zemSelectionService.init();
        locationSpy.and.callThrough();
        zemSelectionService.unselectTotals();
        expect(zemSelectionService.getSelection().selected).toEqual([1, 2, 3]);
        expect(zemSelectionService.isTotalsSelected()).toBe(false);
        expect($location.search()).toEqual({
            totals_unselected: true,
            selected_ids: '1,2,3',
        });
    });

    it('should correctly select all', function() {
        var locationSpy = spyOn($location, 'search').and.returnValue({
            selected_ids: '1,2,3',
        });
        zemSelectionService.init();
        locationSpy.and.callThrough();
        zemSelectionService.selectAll();
        expect(zemSelectionService.getSelection().selected).toEqual([]);
        expect(zemSelectionService.isTotalsSelected()).toBe(true);
        expect(zemSelectionService.isAllSelected()).toBe(true);
        expect($location.search()).toEqual({
            selected_all: true,
        });
    });

    it('should correctly unselect all', function() {
        var locationSpy = spyOn($location, 'search').and.returnValue({
            selected_totals: true,
            selected_all: true,
        });
        zemSelectionService.init();
        locationSpy.and.callThrough();
        zemSelectionService.unselectAll();
        expect(zemSelectionService.isTotalsSelected()).toBe(true);
        expect(zemSelectionService.isAllSelected()).toBe(false);
        expect($location.search()).toEqual({});
    });
});
