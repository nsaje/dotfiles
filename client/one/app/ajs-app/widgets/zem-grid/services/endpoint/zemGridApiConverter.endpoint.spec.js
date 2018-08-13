/* eslint-disable camelcase */

describe('zemGridEndpointApiConverter', function() {
    var zemGridEndpointApiConverter,
        config,
        breakdown,
        metaData,
        expectedResult;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function(_zemGridEndpointApiConverter_) {
        zemGridEndpointApiConverter = _zemGridEndpointApiConverter_;
    }));

    it('should correctly convert grouped rows', function() {
        config = {
            level: 1,
            breakdown: [{query: 'ad_group'}],
        };
        breakdown = {
            rows: [
                {
                    breakdown_id: '1',
                    breakdown_name: 'Test breakdown 1',
                },
                {
                    breakdown_id: '2',
                    breakdown_name: 'Test breakdown 2',
                },
                {
                    breakdown_id: '3',
                    breakdown_name: 'Test breakdown 1',
                    group: {
                        ids: ['2', '4'],
                    },
                },
                {
                    breakdown_id: '4',
                    breakdown_name: 'Test breakdown 4',
                },
            ],
        };
        metaData = {
            breakdown: 'ad_group',
            columns: [
                {
                    field: 'breakdown_name',
                    type: 'breakdown',
                },
            ],
            categories: [],
        };

        var expected = {
            level: 1,
            rows: [
                {
                    stats: {
                        breakdown_name: {
                            value: 'Test breakdown 1',
                            text: undefined,
                            url: undefined,
                            redirectorUrl: undefined,
                        },
                    },
                    group: undefined,
                    breakdownId: '1',
                    archived: undefined,
                    supplyDashDisabledMessage: undefined,
                    entity: {type: 'adGroup', id: 1},
                },
                {
                    stats: {
                        breakdown_name: {
                            value: 'Test breakdown 1',
                            text: undefined,
                            url: undefined,
                            redirectorUrl: undefined,
                        },
                    },
                    group: {ids: ['2', '4']},
                    breakdownId: '3',
                    archived: undefined,
                    supplyDashDisabledMessage: undefined,
                    entity: {type: 'adGroup', id: 3},
                    breakdown: {
                        breakdownId: '3',
                        group: true,
                        meta: {},
                        level: 1,
                        rows: [
                            {
                                stats: {
                                    breakdown_name: {
                                        value: 'Test breakdown 2',
                                        text: undefined,
                                        url: undefined,
                                        redirectorUrl: undefined,
                                    },
                                },
                                group: undefined,
                                breakdownId: '2',
                                archived: undefined,
                                supplyDashDisabledMessage: undefined,
                                entity: {type: 'adGroup', id: 2},
                            },
                            {
                                stats: {
                                    breakdown_name: {
                                        value: 'Test breakdown 4',
                                        text: undefined,
                                        url: undefined,
                                        redirectorUrl: undefined,
                                    },
                                },
                                group: undefined,
                                breakdownId: '4',
                                archived: undefined,
                                supplyDashDisabledMessage: undefined,
                                entity: {type: 'adGroup', id: 4},
                            },
                        ],
                        pagination: {complete: true},
                    },
                },
            ],
        };

        var convertedBreakdown = zemGridEndpointApiConverter.convertBreakdownFromApi(
            config,
            breakdown,
            metaData
        );
        expect(convertedBreakdown).toEqual(expected);
    });
    it('should correctly convert breakdown object', function() {
        config = {
            level: 2,
            breakdown: [{query: 'campaign'}, {query: 'ad_group'}],
        };

        breakdown = {
            rows: [
                {
                    breakdown_id: '3||33',
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
                    breakdown_id: '4||44',
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
                    breakdown_id: '5||55',
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
            breakdown: 'content_ad',
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
            categories: [
                {
                    name: 'category 1',
                    fields: ['clicks', 'state'],
                },
            ],
        };

        expectedResult = {
            rows: [
                {
                    stats: {
                        breakdown_name: {
                            value: 'Test breakdown 1',
                            text: 'Example 1',
                            url: 'example1.com',
                            redirectorUrl: 'redirector.example1.com',
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
                        domain_link: {
                            url: 'domainlink.com',
                        },
                        supply_dash_url: {
                            url: 'supplydashurl.com',
                        },
                    },
                    breakdownId: '3||33',
                    group: undefined,
                    archived: false,
                    supplyDashDisabledMessage: 'Disabled',
                    entity: {
                        type: 'adGroup',
                        id: 33,
                    },
                },
                {
                    stats: {
                        breakdown_name: {
                            value: 'Test breakdown 2',
                            text: 'Example 2',
                            url: 'example2.com',
                            redirectorUrl: null,
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
                        domain_link: {
                            url: 'domainlink.com',
                        },
                        supply_dash_url: {
                            url: 'supplydashurl.com',
                        },
                    },
                    breakdownId: '4||44',
                    group: undefined,
                    archived: false,
                    supplyDashDisabledMessage: undefined,
                    entity: {
                        type: 'adGroup',
                        id: 44,
                    },
                },
                {
                    stats: {
                        breakdown_name: {
                            value: 'Test breakdown 3',
                            text: 'Example 3',
                            url: null,
                            redirectorUrl: null,
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
                        domain_link: {
                            url: 'domainlink.com',
                        },
                        supply_dash_url: {
                            url: 'supplydashurl.com',
                        },
                    },
                    breakdownId: '5||55',
                    group: undefined,
                    archived: true,
                    supplyDashDisabledMessage: undefined,
                    entity: {
                        type: 'adGroup',
                        id: 55,
                    },
                },
            ],
            totals: {
                breakdown_name: {
                    value: undefined,
                    text: undefined,
                    url: undefined,
                    redirectorUrl: undefined,
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

        var convertedBreakdown = zemGridEndpointApiConverter.convertBreakdownFromApi(
            config,
            breakdown,
            metaData
        );
        expect(convertedBreakdown).toEqual(expectedResult);
    });

    it('should correctly convert config object to api', function() {
        var startDate = moment('2016-05-17');
        var endDate = moment('2016-06-14');

        config = {
            breakdownParents: [],
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
            parents: [],
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

        var convertedConfig = zemGridEndpointApiConverter.convertConfigToApi(
            config
        );
        expect(convertedConfig).toEqual(expectedResult);
    });
});
/* eslint-enable camelcase */
