import * as arrayHelpers from './array.helpers';

describe('ArrayHelpers', () => {
    it('should correctly check if array is empty', () => {
        expect(arrayHelpers.isEmpty(null)).toEqual(true);
        expect(arrayHelpers.isEmpty(undefined)).toEqual(true);
        expect(arrayHelpers.isEmpty([])).toEqual(true);
        expect(arrayHelpers.isEmpty([1, 2, 3])).toBeFalse();
        expect(arrayHelpers.isEmpty(['Item 1', 'Item 2', 'Item 3'])).toEqual(
            false
        );
    });

    it('should find an intersection of two arrays', () => {
        expect(arrayHelpers.intersect([1, 2, 3, 4], [3, 4, 5, 6])).toEqual([
            3,
            4,
        ]);
        expect(arrayHelpers.intersect(['test'], ['test'])).toEqual(['test']);
        expect(
            arrayHelpers.intersect(['one', 'two'], ['two', 'three'])
        ).toEqual(['two']);
    });

    it("should return an empty array if two arrays don't intersect", () => {
        expect(arrayHelpers.intersect([], [1, 2, 3])).toEqual([]);
        expect(arrayHelpers.intersect([1, 2, 3], [])).toEqual([]);
        expect(arrayHelpers.intersect([1, 2, 3], [4, 5, 6])).toEqual([]);
    });

    it('should return an empty intersection if one or both arrays are null or undefined', () => {
        expect(arrayHelpers.intersect(null, null)).toEqual([]);
        expect(arrayHelpers.intersect(null, undefined)).toEqual([]);
        expect(arrayHelpers.intersect(null, [1, 2, 3])).toEqual([]);
        expect(arrayHelpers.intersect(undefined, null)).toEqual([]);
        expect(arrayHelpers.intersect(undefined, undefined)).toEqual([]);
        expect(arrayHelpers.intersect(undefined, [1, 2, 3])).toEqual([]);
        expect(arrayHelpers.intersect([1, 2, 3], null)).toEqual([]);
        expect(arrayHelpers.intersect([1, 2, 3], undefined)).toEqual([]);
    });

    it('should find an intersection of two arrays of complex objects even when they are not passed by reference', () => {
        const xxx = {this: 'is', a: {very: ['complex', 'object']}};
        expect(arrayHelpers.intersect([xxx], [xxx])).toEqual([xxx]);

        expect(
            arrayHelpers.intersect(
                [{this: 'is', a: {very: ['complex', 'object']}}],
                [{this: 'is', a: {very: ['complex', 'object']}}]
            )
        ).toEqual([{this: 'is', a: {very: ['complex', 'object']}}]);
        expect(
            arrayHelpers.intersect(
                [{this: 'is', a: {very: ['complex', 'object']}}],
                [{this: 'is', another: {very: ['complex', 'object']}}]
            )
        ).toEqual([]);
    });

    it('should check if one array contains any elements of the other', () => {
        expect(arrayHelpers.includesAny([], [1, 2, 3])).toBeFalse();
        expect(arrayHelpers.includesAny([1, 2, 3], [])).toBeFalse();
        expect(arrayHelpers.includesAny([1, 2, 3], [4, 5, 6])).toBeFalse();
        expect(arrayHelpers.includesAny([1, 2, 3, 4], [3, 4, 5, 6])).toBeTrue();
        expect(arrayHelpers.includesAny(['test'], ['test'])).toBeTrue();
        expect(
            arrayHelpers.includesAny(['one', 'two'], ['two', 'three'])
        ).toBeTrue();
    });

    it("should find that arrays don't include eachother's elements if either of them is null or undefined", () => {
        expect(arrayHelpers.includesAny(null, null)).toBeFalse();
        expect(arrayHelpers.includesAny(null, undefined)).toBeFalse();
        expect(arrayHelpers.includesAny(null, [1, 2, 3])).toBeFalse();
        expect(arrayHelpers.includesAny(undefined, null)).toBeFalse();
        expect(arrayHelpers.includesAny(undefined, undefined)).toBeFalse();
        expect(arrayHelpers.includesAny(undefined, [1, 2, 3])).toBeFalse();
        expect(arrayHelpers.includesAny([1, 2, 3], null)).toBeFalse();
        expect(arrayHelpers.includesAny([1, 2, 3], undefined)).toBeFalse();
    });

    it('should return distinct values of an array', () => {
        expect(arrayHelpers.distinct([1, 2, 3])).toEqual([1, 2, 3]);
        expect(arrayHelpers.distinct([1, 2, 1, 3])).toEqual([1, 2, 3]);
        expect(arrayHelpers.distinct(['a', 'b', 'c'])).toEqual(['a', 'b', 'c']);
        expect(arrayHelpers.distinct(['a', 'b', 'a', 'c'])).toEqual([
            'a',
            'b',
            'c',
        ]);
    });
});
