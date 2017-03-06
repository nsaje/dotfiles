describe('zemUtils', function () {
    var zemUtils;
    beforeEach(module('one'));
    beforeEach(module('one.mocks.zemInitializationService'));
    beforeEach(inject(function (_zemUtils_) {
        zemUtils = _zemUtils_;
    }));

    it('should correctly convert underscore properties to camelcase', function () {
        var obj = {
            prop: {},
            prop_underscore: 'abcd',
            prop_with_many_underscores: 123,
        };

        var converted = zemUtils.convertToCamelCase(obj);
        expect(converted).toEqual({
            prop: {},
            propUnderscore: 'abcd',
            propWithManyUnderscores: 123
        });
    });

    it('should correctly convert underscore properties to camelcase (recursively)', function () {
        var obj = {
            prop: 1,
            complex_prop: {
                prop: 1,
                prop_underscore: 2,
                another_complex_prop: {
                    prop: 1,
                    prop_underscore: 2,
                }
            },
        };

        var converted = zemUtils.convertToCamelCase(obj);
        expect(converted).toEqual({
            prop: 1,
            complexProp: {
                prop: 1,
                propUnderscore: 2,
                anotherComplexProp: {
                    prop: 1,
                    propUnderscore: 2,
                }
            },
        });
    });

    it('should correctly convert camelcase properties to underscore format', function () {
        var obj = {
            simple: {},
            camelCase: 'abcd',
            camelCaseManyTimes: 123,
        };

        var converted = zemUtils.convertToUnderscore(obj);
        expect(converted).toEqual({
            simple: {},
            camel_case: 'abcd',
            camel_case_many_times: 123
        });
    });

    it('should correctly convert underscore properties to camelcase (recursively)', function () {
        var obj = {
            prop: 1,
            complexProp: {
                prop: 1,
                propCamelCase: 2,
                anotherComplexProp: {
                    prop: 1,
                    propCamelCase: 2,
                }
            },
        };

        var converted = zemUtils.convertToUnderscore(obj);
        expect(converted).toEqual({
            prop: 1,
            complex_prop: {
                prop: 1,
                prop_camel_case: 2,
                another_complex_prop: {
                    prop: 1,
                    prop_camel_case: 2,
                }
            },
        });
    });
});
