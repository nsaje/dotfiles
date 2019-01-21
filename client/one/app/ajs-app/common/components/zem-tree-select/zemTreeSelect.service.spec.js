describe('zemTreeSelectService', function() {
    var zemTreeSelectService;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function(_zemTreeSelectService_) {
        zemTreeSelectService = _zemTreeSelectService_;
    }));

    it('should return a list of visible items', function() {
        expect(
            zemTreeSelectService.getVisibleItems([
                {isVisible: true},
                {isVisible: true},
                {isVisible: false},
                {isVisible: true},
            ]).length
        ).toBe(3);
    });

    it('should return a list of visible items matching search query with parents expanded', function() {
        var item1 = {
            name: 'first item',
            id: '1',
        };
        var item2 = {
            name: 'second item',
            id: '2',
            parent: item1,
        };
        var item3 = {
            name: 'third item',
            id: '3',
            parent: item1,
        };
        var item4 = {
            name: 'fourth item',
            id: '4',
            parent: item2,
        };

        var visibleElements = zemTreeSelectService.getVisibleItemsMatchingQuery(
            'second',
            [item1, item2, item3, item4]
        );
        expect(visibleElements).toEqual([item1, item2]);
        expect(item1.isCollapsed).toBe(false);
        expect(item2.isCollapsed).toBe(true);
    });

    it('should return a list of items visible by default when search query is empty', function() {
        var item1 = {
            name: 'first item',
            id: '1',
            level: 1,
        };
        var item2 = {
            name: 'second item',
            id: '2',
            parent: item1,
            level: 2,
        };
        var item3 = {
            name: 'third item',
            id: '3',
            level: 1,
        };

        var visibleElements = zemTreeSelectService.getVisibleItemsMatchingQuery(
            '',
            [item1, item2, item3]
        );
        expect(visibleElements).toEqual([item1, item3]);
        expect(item1.isCollapsed).toBe(true);
        expect(item3.isCollapsed).toBe(true);
    });

    it('should return a list of visible items after expanding a parent', function() {
        var parent1 = {
            isVisible: true,
            isCollapsed: true,
        };
        var child11 = {
            parent: parent1,
        };
        var child12 = {
            parent: parent1,
        };
        var grandChild121 = {
            parent: child12,
        };
        var parent2 = {
            isVisible: true,
            isCollapsed: true,
        };
        var child21 = {
            parent: parent2,
        };

        var visibleElements = zemTreeSelectService.getVisibleItemsAfterItemToggled(
            parent1,
            [parent1, child11, child12, grandChild121, parent2, child21]
        );
        expect(visibleElements).toEqual([parent1, child11, child12, parent2]);
        expect(parent1.isCollapsed).toBe(false);
        expect(parent2.isCollapsed).toBe(true);
    });

    it('should return a list of visible items after collapsing a parent', function() {
        var parent1 = {
            isVisible: true,
            isCollapsed: false,
        };
        var child11 = {
            isVisible: true,
            parent: parent1,
        };
        var child12 = {
            isVisible: true,
            isCollapsed: false,
            parent: parent1,
        };
        var grandChild121 = {
            isVisible: true,
            parent: child12,
        };
        var parent2 = {
            isVisible: true,
            isCollapsed: true,
        };
        var child21 = {
            parent: parent2,
        };

        var visibleElements = zemTreeSelectService.getVisibleItemsAfterItemToggled(
            parent1,
            [parent1, child11, child12, grandChild121, parent2, child21]
        );
        expect(visibleElements).toEqual([parent1, parent2]);
        expect(parent1.isCollapsed).toBe(true);
        expect(child12.isCollapsed).toBe(true);
    });
});
