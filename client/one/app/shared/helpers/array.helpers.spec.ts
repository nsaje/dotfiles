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
        expect(arrayHelpers.distinct([{a: 1}, {b: 2}, {c: 3}])).toEqual([
            {a: 1},
            {b: 2},
            {c: 3},
        ]);
        expect(arrayHelpers.distinct([{a: 1}, {b: 2}, {a: 1}])).toEqual([
            {a: 1},
            {b: 2},
        ]);
        expect(
            arrayHelpers.distinct([{a: 1}, {b: 2}, {a: 1}, {c: 3}])
        ).toEqual([{a: 1}, {b: 2}, {c: 3}]);
    });

    it('should split an array of objects based on some property', () => {
        const objects: {id: number; value: string}[] = [
            {id: 1, value: 'one'},
            {id: 2, value: 'prime'},
            {id: 3, value: 'prime'},
            {id: 4, value: 'even'},
            {id: 5, value: 'prime'},
            {id: 6, value: 'even'},
            {id: 7, value: 'prime'},
            {id: 8, value: 'even'},
            {id: 9, value: 'odd'},
        ];

        expect(arrayHelpers.groupArray([], x => x.value)).toEqual([]);
        expect(arrayHelpers.groupArray(objects, x => x.value)).toEqual([
            [{id: 1, value: 'one'}],
            [
                {id: 2, value: 'prime'},
                {id: 3, value: 'prime'},
                {id: 5, value: 'prime'},
                {id: 7, value: 'prime'},
            ],
            [
                {id: 4, value: 'even'},
                {id: 6, value: 'even'},
                {id: 8, value: 'even'},
            ],
            [{id: 9, value: 'odd'}],
        ]);
    });

    it('should check if two arrays contain the same elements, regardless of ordering', () => {
        const a = 1;
        const b = 'b';
        const c = {what: 'ever'};

        const array1 = [a, b, c];
        const array2 = [b, c, a];

        expect(
            arrayHelpers.arraysContainSameElements(array1, array2)
        ).toBeTrue();
        expect(
            arrayHelpers.arraysContainSameElements([1, 2, 3], [3, 1, 2])
        ).toBeTrue();
        expect(
            arrayHelpers.arraysContainSameElements(
                ['three', 'one', 'two'],
                ['one', 'two', 'three']
            )
        ).toBeTrue();
        expect(
            arrayHelpers.arraysContainSameElements([1, 2, 3, 4], [3, 4, 5, 6])
        ).toBeFalse();
        expect(
            arrayHelpers.arraysContainSameElements(
                ['one', 'two'],
                ['two', 'three']
            )
        ).toBeFalse();
    });

    it('should correctly reduce array to object', () => {
        expect(arrayHelpers.arrayToObject(null)).toEqual(null);
        expect(arrayHelpers.arrayToObject(undefined)).toEqual(undefined);
        expect(arrayHelpers.arrayToObject({})).toEqual({});
        expect(arrayHelpers.arrayToObject([])).toEqual({});
        expect(
            arrayHelpers.arrayToObject({email: ['Enter a valid email address']})
        ).toEqual({
            email: ['Enter a valid email address'],
        });
        expect(
            arrayHelpers.arrayToObject([
                {},
                {email: ['Enter a valid email address']},
                {},
                {
                    email: ['Enter a valid email address'],
                    address: ['Enter a valid address'],
                },
                {},
            ])
        ).toEqual({
            email: ['Enter a valid email address'],
            address: ['Enter a valid address'],
        });
    });

    it('should correctly replace an array item', () => {
        const mockedOldItems = [
            {
                id: 1,
                name: 'One',
            },
            {
                id: 2,
                name: 'Two',
            },
            {
                id: 3,
                name: 'Three',
            },
        ];
        const mockedDifferentItems = [
            {
                id: 4,
                name: 'Four',
            },
            {
                id: 5,
                name: 'Five',
            },
            {
                id: 6,
                name: 'Six',
            },
        ];
        const mockedNewItem = {
            id: 2,
            name: 'II',
        };
        const mockedNewItems = [
            {
                id: 1,
                name: 'One',
            },
            {
                id: 2,
                name: 'II',
            },
            {
                id: 3,
                name: 'Three',
            },
        ];
        const mockedIdGetter = (item: {id: number; name: string}) => item.id;

        expect(
            arrayHelpers.replaceArrayItem(null, mockedIdGetter, mockedNewItem)
        ).toEqual(null);
        expect(
            arrayHelpers.replaceArrayItem(
                undefined,
                mockedIdGetter,
                mockedNewItem
            )
        ).toEqual(undefined);
        expect(
            arrayHelpers.replaceArrayItem([], mockedIdGetter, mockedNewItem)
        ).toEqual([]);
        expect(
            arrayHelpers.replaceArrayItem(
                mockedDifferentItems,
                mockedIdGetter,
                mockedNewItem
            )
        ).toEqual(mockedDifferentItems);
        expect(
            arrayHelpers.replaceArrayItem(
                mockedOldItems,
                mockedIdGetter,
                mockedNewItem
            )
        ).toEqual(mockedNewItems);
    });
});
