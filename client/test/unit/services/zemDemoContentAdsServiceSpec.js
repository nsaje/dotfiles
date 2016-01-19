'use strict';

describe('zemDemoContentAdsService', function() {
    var contentAdsService = null;
    
    beforeEach(module('one'));
    beforeEach(inject(function(_zemDemoContentAdsService_) {
        contentAdsService = _zemDemoContentAdsService_;
    }));

    it('set and apply for content ad', function () {
        expect(contentAdsService.apply(1, 1, {})).toEqual({});
        expect(contentAdsService.apply(1, 1, { test: 1 })).toEqual({test: 1});
        contentAdsService.set(1, 1, { test: 2 });
        expect(contentAdsService.apply(1, 1, { test: 1 })).toEqual({test: 2});
        contentAdsService.set(1, 1, { test1: 1 });
        expect(
            contentAdsService.apply(1, 1, { test: 1 })
        ).toEqual({test: 2, test1: 1});
               expect(contentAdsService.apply(2, 2, {})).toEqual({});
    });
    it('set bulk info for content ad', function () {
        contentAdsService.setBulk(1, [1, 2, 3], false, false, { test: 1 });
        expect(
            contentAdsService.apply(1, 4, { something: 1})
        ).toEqual(
            { something: 1}
        );
        expect(
            contentAdsService.apply(1, 1, { something: 2 })
        ).toEqual({ something: 2, test: 1 });

        // bulk sets some kind of "defaults"
        contentAdsService.setBulk(1, false, false, true, { test: 1 });
        expect(
            contentAdsService.apply(1, 1, { something: 2 })
        ).toEqual({ something: 2, test: 1 });
        expect(
            contentAdsService.apply(1, 4, { something: 2 })
        ).toEqual({ something: 2, test: 1 });

        // specific overwrite bulk
        contentAdsService.setBulk(1, [4, 5], false, true, { test: 2 });
        expect(
            contentAdsService.apply(1, 3, { something: 2 })
        ).toEqual({ something: 2, test: 2 });
        expect(
            contentAdsService.apply(1, 5, { something: 2 })
        ).toEqual({ something: 2, test: 2 });
        
        contentAdsService.setBulk(1, [4, 5], false, false, { test: 3 });
        expect(
            contentAdsService.apply(1, 3, { something: 2 })
        ).toEqual({ something: 2, test: 2 });
        expect(
            contentAdsService.apply(1, 5, { something: 2 })
        ).toEqual({ something: 2, test: 3 });
    });
    it('set bulk info for content ad with excluded ids', function () {
        contentAdsService.setBulk(1, false, [2, 3], true, { test1: 1 });
        expect(
            contentAdsService.apply(1, 1, { something: 2 })
        ).toEqual({ something: 2,  test1: 1 });
        expect(
            contentAdsService.apply(1, 2, { something: 2 })
        ).toEqual({ something: 2} );

        // excludes with  the same key are always overwritten
        contentAdsService.setBulk(1, false, [3], true, { test1: 2 });
        expect(
            contentAdsService.apply(1, 1, { something: 2 })
        ).toEqual({ something: 2,  test1: 2 });
        expect(
            contentAdsService.apply(1, 2, { something: 2 })
        ).toEqual({ something: 2,  test1: 2 });
        expect(
            contentAdsService.apply(1, 3, { something: 2 })
        ).toEqual({ something: 2} );

        // different key  does not overwrite excludes
        contentAdsService.setBulk(1, false, [2], true, { test2: 2 });
        expect(
            contentAdsService.apply(1, 1, { something: 2 })
        ).toEqual({ something: 2,  test1: 2, test2: 2 });
        expect(
            contentAdsService.apply(1, 2, { something: 2 })
        ).toEqual({ something: 2,  test1: 2 });
        expect(
            contentAdsService.apply(1, 3, { something: 2 })
        ).toEqual({ something: 2, test2: 2 });

        // and no excludes with same keys reset everything
        contentAdsService.setBulk(1, false, false, true, { test1: 1, test2: 1 });
        expect(
            contentAdsService.apply(1, 1, { something: 2 })
        ).toEqual({ something: 2,  test1: 1, test2: 1 });
        expect(
            contentAdsService.apply(1, 2, { something: 2 })
        ).toEqual({ something: 2,  test1: 1, test2: 1 });
        expect(
            contentAdsService.apply(1, 3, { something: 2 })
        ).toEqual({ something: 2,  test1: 1, test2: 1 });
    });
    it('set bulk info for content ad with excluded and included ids', function () {
        contentAdsService.setBulk(1, [1], [2], true, { test1: 1, test2: 1 });
        expect(
            contentAdsService.apply(1, 1, { something: 2 })
        ).toEqual({ something: 2,  test1: 1, test2: 1 });
        expect(
            contentAdsService.apply(1, 2, { something: 2 })
        ).toEqual({ something: 2 } );
        expect(
            contentAdsService .apply(1, 3, { something: 2 })
        ).toEqual({ something: 2,  test1: 1, test2: 1 });
    });
});
