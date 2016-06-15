/* globals describe, it, beforeEach, expect, module, inject, moment */

/* eslint-disable camelcase */
describe('test zemGridEndpointApiConverter', function () {
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
        };

        metaData = {
            columns: {
                clicks: {
                    field: 'clicks',
                    type: 'number',
                },
                state: {
                    field: 'state',
                    type: 'state',
                },
            },
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
                        unknown: {
                            value: null,
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
        };

        zemGridEndpointApiConverter.convertFromApi(config, breakdown, metaData);
        expect(breakdown).toEqual(expectedResult);
    });

    it('should correctly convert config object to api', function () {
        var startDate = moment('2016-05-17');
        var endDate = moment('2016-06-14');

        config = {
            breakdownPage: [],
            breakdown: [{name: 'By Ad Group', query: 'ad_group'}],
            startDate: startDate,
            endDate: endDate,
        };

        expectedResult = {
            breakdown_page: [],
            startDate: startDate,
            start_date: '2016-05-17',
            endDate: endDate,
            end_date: '2016-06-14',
        };

        zemGridEndpointApiConverter.convertToApi(config);
        expect(config).toEqual(expectedResult);
    });
});
/* eslint-enable camelcase */
