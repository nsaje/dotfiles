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
                    url: 'example1.com',
                    redirector_url: 'redirector.example1.com',
                    title: 'Example 1',
                    domain_link: 'domainlink.com',
                    supply_dash_url: 'supplydashurl.com',
                    supply_dash_disabled_message: 'Disabled',
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
                    url: 'example2.com',
                    redirector_url: '',
                    title: 'Example 2',
                    domain_link: 'domainlink.com',
                    supply_dash_url: 'supplydashurl.com',
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
                    url: '',
                    redirector_url: '',
                    title: 'Example 3',
                    domain_link: 'domainlink.com',
                    supply_dash_url: 'supplydashurl.com',
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
                    field: 'domain_link',
                    type: 'visibleLink',
                },
                {
                    field: 'supply_dash_url',
                    type: 'link',
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
                        urlLink: {
                            text: 'example1.com',
                            url: 'example1.com',
                        },
                        titleLink: {
                            text: 'Example 1',
                            url: 'example1.com',
                            redirectorUrl: 'redirector.example1.com',
                        },
                        domain_link: {
                            url: 'domainlink.com',
                        },
                        supply_dash_url: {
                            url: 'supplydashurl.com',
                        },
                    },
                    breakdownId: 3,
                    archived: false,
                    supplyDashDisabledMessage: 'Disabled',
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
                        urlLink: {
                            text: 'example2.com',
                            url: 'example2.com',
                        },
                        titleLink: {
                            text: 'Example 2',
                            url: 'example2.com',
                            redirectorUrl: null,
                        },
                        domain_link: {
                            url: 'domainlink.com',
                        },
                        supply_dash_url: {
                            url: 'supplydashurl.com',
                        },
                    },
                    breakdownId: 4,
                    archived: false,
                    supplyDashDisabledMessage: undefined,
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
                        urlLink: {
                            text: 'N/A',
                            url: null,
                        },
                        titleLink: {
                            text: 'Example 3',
                            url: null,
                            redirectorUrl: null,
                        },
                        domain_link: {
                            url: 'domainlink.com',
                        },
                        supply_dash_url: {
                            url: 'supplydashurl.com',
                        },
                    },
                    breakdownId: 5,
                    archived: true,
                    supplyDashDisabledMessage: undefined,
                },
            ],
            totals: {
                breakdown_name: {
                    value: undefined,
                },
                clicks: {
                    value: 1000,
                },
                state: {
                    value: undefined,
                },
                domain_link: {
                    url: undefined,
                },
                supply_dash_url: {
                    url: undefined,
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
            showArchived: true,
            showBlacklistedPublishers: false,
            filteredAgencies: [1],
            filteredAccountTypes: [1, 2],
            filteredSources: [1, 2, 3],
            level: 1,
            limit: 20,
            offset: 0,
            order: 'field',
        };

        expectedResult = {
            breakdown_page: [],
            start_date: '2016-05-17',
            end_date: '2016-06-14',
            show_archived: true,
            show_blacklisted_publishers: false,
            filtered_agencies: [1],
            filtered_account_types: [1, 2],
            filtered_sources: [1, 2, 3],
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
