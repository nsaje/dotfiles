import * as commonHelpers from './common.helpers';

describe('commonHelpers', () => {
    it('should correctly check if value is defined', () => {
        expect(commonHelpers.isDefined(null)).toEqual(false);
        expect(commonHelpers.isDefined(undefined)).toEqual(false);
        expect(commonHelpers.isDefined('Test')).toEqual(true);
        expect(commonHelpers.isDefined(123)).toEqual(true);
    });

    it('should correctly return value if defined, otherwise should return default', () => {
        expect(commonHelpers.getValueOrDefault(999, 123)).toEqual(999);
        expect(commonHelpers.getValueOrDefault(null, 123)).toEqual(123);
        expect(commonHelpers.getValueOrDefault('Test', 'Default')).toEqual(
            'Test'
        );
        expect(commonHelpers.getValueOrDefault(undefined, 'Default')).toEqual(
            'Default'
        );
    });

    it('should correctly check if value is defined and has value', () => {
        expect(commonHelpers.isNotEmpty(null)).toEqual(false);
        expect(commonHelpers.isNotEmpty(undefined)).toEqual(false);

        expect(commonHelpers.isNotEmpty('')).toEqual(false);
        expect(commonHelpers.isNotEmpty('Test')).toEqual(true);
        expect(commonHelpers.isNotEmpty(123)).toEqual(true);

        expect(commonHelpers.isNotEmpty({})).toEqual(false);
        expect(
            commonHelpers.isNotEmpty({
                name: 'Test',
            })
        ).toEqual(true);

        expect(commonHelpers.isNotEmpty([])).toEqual(false);
        expect(commonHelpers.isNotEmpty(['Test1', 'Test2'])).toEqual(true);

        expect(commonHelpers.isNotEmpty(-1)).toEqual(true);
        expect(commonHelpers.isNotEmpty(0)).toEqual(true);
        expect(commonHelpers.isNotEmpty(1)).toEqual(true);
    });

    it('should correctly check if value is equal to any item', () => {
        expect(commonHelpers.isEqualToAnyItem(null, [null, '1'])).toEqual(true);
        expect(commonHelpers.isEqualToAnyItem(null, [1, '2'])).toEqual(false);
        expect(commonHelpers.isEqualToAnyItem(1, null)).toEqual(false);
        expect(commonHelpers.isEqualToAnyItem(1, ['1', 2, 3])).toEqual(false);
        expect(commonHelpers.isEqualToAnyItem(1, [1, 2, 3])).toEqual(true);
        expect(
            commonHelpers.isEqualToAnyItem('Generic comment', [
                1,
                2,
                'Generic comment',
            ])
        ).toEqual(true);
    });
});
