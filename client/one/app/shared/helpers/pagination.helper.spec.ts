import * as paginationHelpers from './pagination.helper';

describe('paginationHelpers', () => {
    it('should correctly compute offset from page and page size', () => {
        expect(paginationHelpers.getOffset(1, 20)).toEqual(0);
        expect(paginationHelpers.getOffset(2, 20)).toEqual(20);
        expect(paginationHelpers.getOffset(3, 20)).toEqual(40);
        expect(paginationHelpers.getOffset(4, 20)).toEqual(60);
        expect(paginationHelpers.getOffset(5, 20)).toEqual(80);

        expect(paginationHelpers.getOffset(1, 50)).toEqual(0);
        expect(paginationHelpers.getOffset(2, 50)).toEqual(50);
        expect(paginationHelpers.getOffset(3, 50)).toEqual(100);
        expect(paginationHelpers.getOffset(4, 50)).toEqual(150);
        expect(paginationHelpers.getOffset(5, 50)).toEqual(200);

        expect(paginationHelpers.getOffset(1, 100)).toEqual(0);
        expect(paginationHelpers.getOffset(2, 100)).toEqual(100);
        expect(paginationHelpers.getOffset(3, 100)).toEqual(200);
        expect(paginationHelpers.getOffset(4, 100)).toEqual(300);
        expect(paginationHelpers.getOffset(5, 100)).toEqual(400);
    });
});
