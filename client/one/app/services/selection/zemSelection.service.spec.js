describe('zemSelectionService', function () {
    var $location;
    var zemSelectionService;

    beforeEach(module('one'));
    beforeEach(inject(function (_$location_, _zemSelectionService_) {
        $location = _$location_;
        zemSelectionService = _zemSelectionService_;
    }));

    it('should init correctly without URL params', function () {
        zemSelectionService.init();
        expect(zemSelectionService.getSelection()).toEqual({
            selected: [],
            unselected: [],
            totals: false,
            all: false,
            batch: null,
        });
    });

    it('should init correctly with URL params', function () {
        spyOn($location, 'search').and.returnValue({
            selected_ids: '1,2,3,whatever,',
            unselected_ids: '4,5,6,:)',
            selected_totals: true,
            selected_all: true,
            selected_batch_id: '999'
        });
        zemSelectionService.init();
        expect(zemSelectionService.getSelection()).toEqual({
            selected: [1, 2, 3],
            unselected: [4, 5, 6],
            totals: true,
            all: true,
            batch: 999,
        });
    });

    it('should correctly determine if selected list is set', function () {
        spyOn($location, 'search').and.returnValue({
            selected_ids: '1,2,3',
        });
        zemSelectionService.init();
        expect(zemSelectionService.isSelectedSet()).toBe(true);
    });

    it('should correctly determine if selected list is not set', function () {
        spyOn($location, 'search').and.returnValue({});
        zemSelectionService.init();
        expect(zemSelectionService.isSelectedSet()).toBe(false);
    });

    it('should correctly determine if unselected list is set', function () {
        spyOn($location, 'search').and.returnValue({
            unselected_ids: '1,2,3',
        });
        zemSelectionService.init();
        expect(zemSelectionService.isUnselectedSet()).toBe(true);
    });

    it('should correctly determine if unselected list is not set', function () {
        spyOn($location, 'search').and.returnValue({});
        zemSelectionService.init();
        expect(zemSelectionService.isUnselectedSet()).toBe(false);
    });

    it('should correctly determine if an id is selected', function () {
        spyOn($location, 'search').and.returnValue({
            selected_ids: '1',
        });
        zemSelectionService.init();
        expect(zemSelectionService.isIdSelected(1)).toBe(true);
        expect(zemSelectionService.isIdSelected(2)).toBe(false);
    });

    it('should correctly determine if an id is selected when when all is selected', function () {
        spyOn($location, 'search').and.returnValue({
            selected_ids: '1',
            selected_all: true,
        });
        zemSelectionService.init();
        expect(zemSelectionService.isIdSelected(1)).toBe(true);
        expect(zemSelectionService.isIdSelected(2)).toBe(true);
    });

    it('should correctly determine if an id is selected when when all is selected and unselected is set', function () { // eslint-disable-line max-len
        spyOn($location, 'search').and.returnValue({
            selected_ids: '1',
            unselected_ids: '3',
            selected_all: true,
        });
        zemSelectionService.init();
        expect(zemSelectionService.isIdSelected(1)).toBe(true);
        expect(zemSelectionService.isIdSelected(2)).toBe(true);
        expect(zemSelectionService.isIdSelected(3)).toBe(false);
    });

    it('should correctly determine if an id is unselected', function () {
        spyOn($location, 'search').and.returnValue({
            unselected_ids: '1',
        });
        zemSelectionService.init();
        expect(zemSelectionService.isIdUnselected(1)).toBe(true);
        expect(zemSelectionService.isIdUnselected(2)).toBe(false);
    });

    it('should return false if totals is not selected', function () {
        expect(zemSelectionService.isTotalsSelected(2)).toBe(false);
    });

    it('should return true if totals are selected', function () {
        spyOn($location, 'search').and.returnValue({
            selected_totals: true,
        });
        zemSelectionService.init();
        expect(zemSelectionService.isTotalsSelected(2)).toBe(true);
    });

    it('should correctly toggle ids', function () {
        var locationSpy = spyOn($location, 'search').and.returnValue({
            selected_ids: '1,2,3',
        });
        zemSelectionService.init();
        locationSpy.and.callThrough();
        zemSelectionService.toggle([1, 2, 3, 4, 5, 6]);
        expect(zemSelectionService.getSelection().selected).toEqual([4, 5, 6]);
        expect($location.search()).toEqual({
            selected_ids: '4,5,6',
        });
    });

    it('should correctly add number id', function () {
        zemSelectionService.add(123);
        expect(zemSelectionService.getSelection().selected).toEqual([123]);
        expect($location.search()).toEqual({
            selected_ids: '123',
        });
    });

    it('should correctly add string id', function () {
        zemSelectionService.add('456');
        expect(zemSelectionService.getSelection().selected).toEqual([456]);
        expect($location.search()).toEqual({
            selected_ids: '456',
        });
    });

    it('should correctly add array of ids', function () {
        zemSelectionService.add([7, 8, '9']);
        expect(zemSelectionService.getSelection().selected).toEqual([7, 8, 9]);
        expect($location.search()).toEqual({
            selected_ids: '7,8,9',
        });
    });

    it('should correctly remove number id', function () {
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

    it('should correctly remove string id', function () {
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

    it('should correctly remove array of ids', function () {
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

    it('should add id to unselected when removing it and all is selected', function () {
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

    it('should add id to unselected when removing it and batch is selected', function () {
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

    it('should correctly toggle totals', function () {
        zemSelectionService.toggleTotals();
        expect(zemSelectionService.getSelection().totals).toBe(true);
        expect($location.search()).toEqual({
            selected_totals: true,
        });
    });

    it('should correctly untoggle totals', function () {
        var locationSpy = spyOn($location, 'search').and.returnValue({
            selected_totals: true,
        });
        zemSelectionService.init();
        locationSpy.and.callThrough();
        zemSelectionService.toggleTotals();
        expect(zemSelectionService.getSelection().totals).toBe(false);
        expect($location.search()).toEqual({});
    });

    it('should correctly toggle all', function () {
        zemSelectionService.toggleAll();
        expect(zemSelectionService.getSelection()).toEqual({
            selected: [],
            unselected: [],
            totals: true,
            all: true,
            batch: null,
        });
        expect($location.search()).toEqual({
            selected_totals: true,
            selected_all: true,
        });
    });

    it('should correctly toggle all if some ids are unselected', function () {
        var locationSpy = spyOn($location, 'search').and.returnValue({
            unselected_ids: '1,2,3',
            selected_totals: true,
            selected_all: true,
        });
        zemSelectionService.init();
        locationSpy.and.callThrough();
        zemSelectionService.toggleAll();
        expect(zemSelectionService.getSelection()).toEqual({
            selected: [],
            unselected: [],
            totals: true,
            all: true,
            batch: null,
        });
        expect($location.search()).toEqual({
            selected_totals: true,
            selected_all: true,
        });
    });

    it('should correctly toggle all if batch is selected', function () {
        var locationSpy = spyOn($location, 'search').and.returnValue({
            selected_batch_id: 999,
        });
        zemSelectionService.init();
        locationSpy.and.callThrough();
        zemSelectionService.toggleAll();
        expect(zemSelectionService.getSelection()).toEqual({
            selected: [],
            unselected: [],
            totals: true,
            all: true,
            batch: null,
        });
        expect($location.search()).toEqual({
            selected_totals: true,
            selected_all: true,
        });
    });

    it('should correctly untoggle all', function () {
        var locationSpy = spyOn($location, 'search').and.returnValue({
            selected_totals: true,
            selected_all: true,
        });
        zemSelectionService.init();
        locationSpy.and.callThrough();
        zemSelectionService.toggleAll();
        expect(zemSelectionService.getSelection()).toEqual({
            selected: [],
            unselected: [],
            totals: false,
            all: false,
            batch: null,
        });
        expect($location.search()).toEqual({});
    });

    it('should correctly select batch', function () {
        var locationSpy = spyOn($location, 'search').and.returnValue({
            unselected_ids: '1,2,3',
            selected_totals: true,
            selected_all: true,
        });
        zemSelectionService.init();
        locationSpy.and.callThrough();
        zemSelectionService.selectBatch(999);
        expect(zemSelectionService.getSelection()).toEqual({
            selected: [],
            unselected: [],
            totals: false,
            all: false,
            batch: 999,
        });
        expect($location.search()).toEqual({
            selected_batch_id: 999,
        });
    });
});
