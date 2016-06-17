/* globals describe, it, beforeEach, expect, module, inject, moment */

/* eslint-disable camelcase */
describe('zemGridEndpointApiConverter', function () {
    var zemGridEndpointApiConverter,
        config,
        breakdown,
        metaData,
        expectedResult;

    beforeEach(module('one'));

    beforeEach(inject(function (_zemGridEndpointApiConverter_) {
        zemGridEndpointApiConverter = _zemGridEndpointApiConverter_;
    }));

    it('should correctly convert breakdown object', function () {
        config = {
            level: 2,
        };

        breakdown = {
            rows: [
                {
                    breakdown_id: 3,
                    parent_breakdown_id: 2,
                    breakdown_name: 'Test breakdown 1',
                    archived: false,
                    editable_fields: {
                        state: {
                            message: null,
                            enabled: true,
                        },
                    },
                    clicks: 100,
                    state: 1,
                    unknown: null,
                },
                {
                    breakdown_id: 4,
                    parent_breakdown_id: 2,
                    breakdown_name: 'Test breakdown 2',
                    archived: false,
                    editable_fields: {
                        state: {
                            message: 'Test edit message.',
                            enabled: false,
                        },
                    },
                    clicks: 200,
                    state: 2,
                },
                {
                    breakdown_id: 5,
                    parent_breakdown_id: 2,
                    breakdown_name: 'Test breakdown 3',
                    archived: true,
                    editable_fields: {
                        state: {
                            message: 'Test edit message.',
                            enabled: false,
                        },
                    },
                    clicks: 300,
                    state: 2,
                },
            ],
            totals: {
                clicks: 1000,
            },
            breakdown_id: 2,
            pagination: {},
        };

        metaData = {
            columns: [
                {
                    field: 'breakdown_name',
                    type: 'breakdown',
                },
                {
                    field: 'clicks',
                    type: 'number',
                },
                {
                    field: 'state',
                    type: 'state',
                },
                {
                    field: 'unknown',
                    type: 'unknown',
                },
            ],
        };

        expectedResult = {
            rows: [
                {
                    stats: {
                        breakdown_name: {
                            value: 'Test breakdown 1',
                        },
                        clicks: {
                            value: 100,
                        },
                        state: {
                            value: 1,
                            isEditable: true,
                            editMessage: null,
                        },
                    },
                    breakdownId: 3,
                    archived: false,
                },
                {
                    stats: {
                        breakdown_name: {
                            value: 'Test breakdown 2',
                        },
                        clicks: {
                            value: 200,
                        },
                        state: {
                            value: 2,
                            isEditable: false,
                            editMessage: 'Test edit message.',
                        },
                    },
                    breakdownId: 4,
                    archived: false,
                },
                {
                    stats: {
                        breakdown_name: {
                            value: 'Test breakdown 3',
                        },
                        clicks: {
                            value: 300,
                        },
                        state: {
                            value: 2,
                            isEditable: false,
                            editMessage: 'Test edit message.',
                        },
                    },
                    breakdownId: 5,
                    archived: true,
                },
            ],
            totals: {
                clicks: {
                    value: 1000,
                },
            },
            breakdownId: 2,
            level: 2,
            pagination: {},
        };

        var convertedBreakdown = zemGridEndpointApiConverter.convertBreakdownFromApi(config, breakdown, metaData);
        expect(convertedBreakdown).toEqual(expectedResult);
    });

    it('should correctly convert config object to api', function () {
        var startDate = moment('2016-05-17');
        var endDate = moment('2016-06-14');

        config = {
            breakdownPage: [],
            breakdown: [{name: 'By Ad Group', query: 'ad_group'}],
            startDate: startDate,
            endDate: endDate,
            level: 1,
            limit: 20,
            offset: 0,
            order: 'field',
        };

        expectedResult = {
            breakdown_page: [],
            start_date: '2016-05-17',
            end_date: '2016-06-14',
            level: 1,
            limit: 20,
            offset: 0,
            order: 'field',
        };

        var convertedConfig = zemGridEndpointApiConverter.convertConfigToApi(config);
        expect(convertedConfig).toEqual(expectedResult);
    });
});
/* eslint-enable camelcase */
