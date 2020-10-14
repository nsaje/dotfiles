import * as entityHelpers from './entity.helpers';

describe('entityHelpers', () => {
    it('should correctly determine if settings has any value', () => {
        let settings: any = [{family: 'CHROME'}];
        expect(entityHelpers.doesAnySettingHaveValue(settings)).toBeTrue();

        settings = ['DESKTOP'];
        expect(entityHelpers.doesAnySettingHaveValue(settings)).toBeTrue();

        settings = 10;
        expect(entityHelpers.doesAnySettingHaveValue(settings)).toBeTrue();

        settings = true;
        expect(entityHelpers.doesAnySettingHaveValue(settings)).toBeTrue();

        settings = false;
        expect(entityHelpers.doesAnySettingHaveValue(settings)).toBeTrue();

        settings = [];
        expect(entityHelpers.doesAnySettingHaveValue(settings)).toBeFalse();

        settings = {};
        expect(entityHelpers.doesAnySettingHaveValue(settings)).toBeFalse();

        settings = null;
        expect(entityHelpers.doesAnySettingHaveValue(settings)).toBeFalse();

        settings = undefined;
        expect(entityHelpers.doesAnySettingHaveValue(settings)).toBeFalse();
    });
});
