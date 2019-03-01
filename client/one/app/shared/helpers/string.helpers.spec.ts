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
});
