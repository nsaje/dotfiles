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
        var defaultStatusTexts = {
            1: 'Active',
            2: 'Paused',
        };
        var publisherStatusTexts = {
            1: 'Active',
            2: 'Blacklisted',
            3: 'Pending',
        };
        tests = [
            {level: 'unknown', breakdown: 'unknown', expectedResult: undefined},
            {level: 'all_accounts', breakdown: 'account', expectedResult: {enabled: 1, paused: 2, statusTexts: defaultStatusTexts}}, // eslint-disable-line max-len
            {level: 'all_accounts', breakdown: 'account', expectedResult: {enabled: 1, paused: 2, statusTexts: defaultStatusTexts}}, // eslint-disable-line max-len
            {level: 'accounts', breakdown: 'campaign', expectedResult: {enabled: 1, paused: 2, statusTexts: defaultStatusTexts}}, // eslint-disable-line max-len
            {level: 'accounts', breakdown: 'campaign', expectedResult: {enabled: 1, paused: 2, statusTexts: defaultStatusTexts}}, // eslint-disable-line max-len
            {level: 'campaigns', breakdown: 'ad_group', expectedResult: {enabled: 1, paused: 2, statusTexts: defaultStatusTexts}}, // eslint-disable-line max-len
            {level: 'campaigns', breakdown: 'ad_group', expectedResult: {enabled: 1, paused: 2, statusTexts: defaultStatusTexts}}, // eslint-disable-line max-len
            {level: 'all_accounts', breakdown: 'source', expectedResult: {enabled: 1, paused: 2, statusTexts: defaultStatusTexts}}, // eslint-disable-line max-len
            {level: 'all_accounts', breakdown: 'source', expectedResult: {enabled: 1, paused: 2, statusTexts: defaultStatusTexts}}, // eslint-disable-line max-len
            {level: 'accounts', breakdown: 'source', expectedResult: {enabled: 1, paused: 2, statusTexts: defaultStatusTexts}}, // eslint-disable-line max-len
            {level: 'accounts', breakdown: 'source', expectedResult: {enabled: 1, paused: 2, statusTexts: defaultStatusTexts}}, // eslint-disable-line max-len
            {level: 'campaigns', breakdown: 'source', expectedResult: {enabled: 1, paused: 2, statusTexts: defaultStatusTexts}}, // eslint-disable-line max-len
            {level: 'campaigns', breakdown: 'source', expectedResult: {enabled: 1, paused: 2, statusTexts: defaultStatusTexts}}, // eslint-disable-line max-len
            {level: 'ad_groups', breakdown: 'source', expectedResult: {enabled: 1, paused: 2, statusTexts: defaultStatusTexts}}, // eslint-disable-line max-len
            {level: 'ad_groups', breakdown: 'source', expectedResult: {enabled: 1, paused: 2, statusTexts: defaultStatusTexts}}, // eslint-disable-line max-len
            {level: 'ad_groups', breakdown: 'publisher', expectedResult: {enabled: 1, blacklisted: 2, pending: 3, statusTexts: publisherStatusTexts}}, // eslint-disable-line max-len
            {level: 'ad_groups', breakdown: 'publisher', expectedResult: {enabled: 1, blacklisted: 2, pending: 3, statusTexts: publisherStatusTexts}}, // eslint-disable-line max-len
        ];

        tests.forEach(function (test) {
            expect(zemGridStateAndStatusHelpers.getStatusValuesAndTexts(test.level, test.breakdown)).toEqual(test.expectedResult);
        });
    });

    it('should retrun correct available state values for level and breakdown', function () {
        tests = [
            {level: 'unknown', breakdown: 'unknown', expectedResult: {enabled: undefined, paused: undefined}},
            {level: 'campaigns', breakdown: 'ad_group', expectedResult: {enabled: 1, paused: 2}},
            {level: 'ad_groups', breakdown: 'content_ad', expectedResult: {enabled: 1, paused: 2}},
            {level: 'ad_groups', breakdown: 'source', expectedResult: {enabled: 1, paused: 2}},
        ];

        tests.forEach(function (test) {
            expect(zemGridStateAndStatusHelpers.getStateValues(test.level, test.breakdown)).toEqual(test.expectedResult);
        });
    });
});
