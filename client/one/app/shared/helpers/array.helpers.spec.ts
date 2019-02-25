import * as arrayHelpers from './array.helpers';

describe('ArrayHelpers', () => {
    it('should correctly check if array is empty', () => {
        expect(arrayHelpers.isEmpty(null)).toEqual(true);
        expect(arrayHelpers.isEmpty(undefined)).toEqual(true);
        expect(arrayHelpers.isEmpty([])).toEqual(true);
        expect(arrayHelpers.isEmpty([1, 2, 3])).toEqual(false);
        expect(arrayHelpers.isEmpty(['Item 1', 'Item 2', 'Item 3'])).toEqual(
            false
        );
    });
});
