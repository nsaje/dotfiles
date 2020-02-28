import * as stringHelpers from './string.helpers';

describe('stringHelpers', () => {
    it('should correctly insert value at specified index', () => {
        expect(stringHelpers.insertStringAtIndex('123', 0, '999')).toEqual(
            '999123'
        );
        expect(stringHelpers.insertStringAtIndex('123', 1, '999')).toEqual(
            '199923'
        );
        expect(stringHelpers.insertStringAtIndex('123', 2, '999')).toEqual(
            '129993'
        );
        expect(stringHelpers.insertStringAtIndex('123', 3, '999')).toEqual(
            '123999'
        );
        expect(stringHelpers.insertStringAtIndex(null, 3, '999')).toEqual(
            '999'
        );
        expect(stringHelpers.insertStringAtIndex(undefined, 3, '999')).toEqual(
            '999'
        );
        expect(stringHelpers.insertStringAtIndex('', 3, '999')).toEqual('999');
    });

    it('should correctly replace value at specified index range', () => {
        expect(
            stringHelpers.replaceStringBetweenIndexes('12345', 0, 1, '999')
        ).toEqual('9992345');

        expect(
            stringHelpers.replaceStringBetweenIndexes('12345', 1, 2, '999')
        ).toEqual('1999345');

        expect(
            stringHelpers.replaceStringBetweenIndexes('12345', 1, 4, '999')
        ).toEqual('19995');

        expect(
            stringHelpers.replaceStringBetweenIndexes('12345', 0, 5, '999')
        ).toEqual('999');

        expect(
            stringHelpers.replaceStringBetweenIndexes('12345', 4, 5, '999')
        ).toEqual('1234999');
    });

    it('should work the same as insertStringAtIndex if both indexes are the same', () => {
        expect(
            stringHelpers.replaceStringBetweenIndexes('12345', 0, 0, '999')
        ).toEqual('99912345');

        expect(
            stringHelpers.replaceStringBetweenIndexes('12345', 2, 2, '999')
        ).toEqual('12999345');

        expect(
            stringHelpers.replaceStringBetweenIndexes('12345', 5, 5, '999')
        ).toEqual('12345999');
    });

    it('should replace the whole string if the string is null, undefined or empty', () => {
        expect(
            stringHelpers.replaceStringBetweenIndexes(null, 2, 2, '999')
        ).toEqual('999');

        expect(
            stringHelpers.replaceStringBetweenIndexes(undefined, 2, 2, '999')
        ).toEqual('999');

        expect(
            stringHelpers.replaceStringBetweenIndexes('', 2, 2, '999')
        ).toEqual('999');
    });

    it('should treat undefined or negative start index as replacing all chars from beginning', () => {
        expect(
            stringHelpers.replaceStringBetweenIndexes('12345', -19, 3, '999')
        ).toEqual('99945');

        expect(
            stringHelpers.replaceStringBetweenIndexes('12345', null, 3, '999')
        ).toEqual('99945');

        expect(
            stringHelpers.replaceStringBetweenIndexes(
                '12345',
                undefined,
                3,
                '999'
            )
        ).toEqual('99945');
    });

    it('should treat undefined or too large end index as replacing all chars to the end', () => {
        expect(
            stringHelpers.replaceStringBetweenIndexes('12345', 1, 9001, '999')
        ).toEqual('1999');

        expect(
            stringHelpers.replaceStringBetweenIndexes('12345', 1, null, '999')
        ).toEqual('1999');

        expect(
            stringHelpers.replaceStringBetweenIndexes(
                '12345',
                1,
                undefined,
                '999'
            )
        ).toEqual('1999');
    });

    it('should treat both undefined or out-of-bounds indexes as replacing the whole string', () => {
        expect(
            stringHelpers.replaceStringBetweenIndexes(
                '12345',
                null,
                undefined,
                '999'
            )
        ).toEqual('999');
    });

    it('should not do anything if startIndex is higher than endIndex', () => {
        expect(
            stringHelpers.replaceStringBetweenIndexes('12345', 3, 2, '999')
        ).toEqual('12345');
    });

    it('should not do anything if startIndex is higher than endIndex', () => {
        expect(
            stringHelpers.replaceStringBetweenIndexes('12345', 3, 2, '999')
        ).toEqual('12345');
    });

    it('should not do anything if startIndex is greater than the string length', () => {
        expect(
            stringHelpers.replaceStringBetweenIndexes('12345', 7, 9, '999')
        ).toEqual('12345');
    });

    it('should not do anything if endIndex is negative', () => {
        expect(
            stringHelpers.replaceStringBetweenIndexes('12345', -3, -2, '999')
        ).toEqual('12345');
    });
});
