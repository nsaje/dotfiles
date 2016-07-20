/* globals describe, it, beforeEach, expect, module, inject */

describe('zemGridStateAndStatusHelpers', function () {
    var zemGridStateAndStatusHelpers,
        tests,
        options;

    beforeEach(module('one'));

    beforeEach(inject(function (_zemGridStateAndStatusHelpers_) {
        zemGridStateAndStatusHelpers = _zemGridStateAndStatusHelpers_;
    }));

    it('should retrun correct status object for level and breakdown', function () {
        // TODO: Tests for other levels and breakdowns
        tests = [
            {field: 'unknown', value: 1, level: 'unknown', breakdown: 'unknown', expectedResult: undefined},
            {field: 'state', value: 1, level: 'campaigns', breakdown: 'ad_group', expectedResult: {value: 1, enabled: 1, paused: 2}}, // eslint-disable-line max-len
            {field: 'status', value: 1, level: 'campaigns', breakdown: 'source', expectedResult: {value: 1, enabled: 1, paused: 2}}, // eslint-disable-line max-len
            {field: 'status_setting', value: 1, level: 'ad_groups', breakdown: 'source', expectedResult: {value: 1, enabled: 1, paused: 2}}, // eslint-disable-line max-len
        ];

        tests.forEach(function (test) {
            var stats = {};
            stats[test.field] = {value: test.value};

            expect(zemGridStateAndStatusHelpers.getRowStatusObject(stats, test.level, test.breakdown)).toEqual(test.expectedResult);
        });
    });

    it('should retrun correct available state values for level and breakdown', function () {
        // TODO: Tests for other levels and breakdowns
        tests = [
            {level: 'unknown', breakdown: 'unknown', expectedResult: {enabled: undefined, paused: undefined}},
            {level: 'campaigns', breakdown: 'ad_group', expectedResult: {enabled: 1, paused: 2}},
            {level: 'ad_groups', breakdown: 'source', expectedResult: {enabled: 1, paused: 2}},
        ];

        tests.forEach(function (test) {
            expect(zemGridStateAndStatusHelpers.getAvailableStateValues(test.level, test.breakdown)).toEqual(test.expectedResult);
        });
    });
});
