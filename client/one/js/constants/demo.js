/*globals angular,oneApp,constants,options,moment*/
'use strict';

oneApp.constant('demoDefaults', {
    newCampaignSettings: function (id) {
        return {
            id: id,
            name: 'New demo campaign',
            accountManager: '1',
            IABCategory: 'IAB1',
            promotionGoal: 1,
            salesRepresentative: '1',
            serviceFee: '20'
        };
    },
    newAdGroupSettings: function (id) {
        return {
            trackingCode: '',
            dailyBudget: '500.00',
            cpc: '0.40',
            state: 2,
            targetRegions: ['US'],
            retargetingAdGroups: [],
            targetDevices: [
                {name: 'Desktop', value: 'desktop', checked: true},
                {name: 'Mobile', value: 'mobile', checked: true}
            ],
            id: id,
            name: 'New demo ad group',
            endDate: null,
            startDate: null,
            contentAdsTabWithCMS: true
        };
    },
    emptyChart: {
        'goals': {},
        'chartData': [
            { 'seriesData': {}, 'id': 'totals', 'name': "Totals"}
        ]
    },
    emptyTable: function () {
        return {
            is_sync_recent: true,
            rows: [],
            pagination: {},
            totals: { 'impressions': 0, 'cost': 0, 'clicks': 0, 'ctr': 0, 'cpc': 0}
        };
    },
    campaignsTableRow: function (name, id) {
        return {
            archived: false,
            name: name,
            avg_tos: 0,
            bounce_rate: 0,
            clicks: 0,
            click_discrepancy: 100,
            cost: 0,
            goals: {},
            cpc: 0,
            ctr: 0,
            impressions: 0,
            last_sync: (new Date()).toISOString(),
            pageviews: 0,
            percent_new_users: 0,
            pv_per_visit: 0,
            state: constants.adGroupSettingsState.ACTIVE,
            unspent_budget: 0,
            visits: 0,
            campaign: id
        };
    },
    accountManagers: [
        {
            'id': '1',
            'name': 'John Smith'
        },
        {
            'id': '2',
            'name': 'Steve Gatsby'
        },
        {
            'id': '3',
            'name': 'Greg Stallone'
        },
        {
            'id': '4',
            'name': 'Olga Moore'
        }
    ],
    budget: function () {
        return {
            'available': 0,
            'total': 0,
            'spend': 0,
            'history': []
        };
    },
    emptySourcesTable: function () {
        return {
            incomplete_postclick_metrics: false,
            is_sync_in_progress: false,
            is_sync_recent: true,
            last_change: (new Date()).toISOString(),
            last_sync: (new Date()).toISOString(),
            notifications: {},
            rows: [],
            totals: {
                avg_tos: 1, current_daily_budget: '', pageviews: 0,
                yesterday_cost: null, visits: 4
            }
        };
    },
    newAdGroupSources: function (all) {
        var skip = {'3': true, '2': true, '4': true, '32': true, '34': true},
            sources = [];
        angular.forEach(all, function (source) {
            if (!skip[source.id] && !source.deprecated) {
                sources.push(source);
                source.canTargetExistingRegions = true;
                source.canRetarget = true;
                source.can_retarget = true;
            }
        });
        return sources;
    },
    newAdGroupSourcesTable: function () {
        return {
            incomplete_postclick_metrics: false,
            is_sync_in_progress: false,
            is_sync_recent: true,
            last_change: (new Date()).toISOString(),
            last_sync: (new Date()).toISOString(),
            notifications: {},
            rows: [
                this.sourcesRow({name: 'Outbrain', id: '3', bid_cpc: '0.18', daily_budget: '2500'}),
                this.sourcesRow({name: 'Gravity', id: '2', bid_cpc: '0.22', daily_budget: '3700'}),
                this.sourcesRow({name: 'Yahoo', id: '4', bid_cpc: '0.13', daily_budget: '1200'}),
                this.sourcesRow({name: 'Yieldmo', id: '32', bid_cpc: '0.15', daily_budget: '2800'}),
                this.sourcesRow({name: 'TripleLift', id: '34', bid_cpc: '0.25', daily_budget: '4000'})
            ],
            totals: {
                avg_tos: 1, current_daily_budget: '', pageviews: 0,
                yesterday_cost: null, visits: 4
            }
        };
    },
    sourcesRow: function (values) {
        var obj = {
            archived: false,
            avg_tos: null,
            bid_cpc: '0.0',
            bounce_rate: null,
            can_edit_budget_and_cpc: true,
            click_discrepancy: null,
            maintenance: false,
            clicks: 0,
            editable_fields: {
                'status_setting': {
                    'message': null,
                    'enabled': true
                },
                'bid_cpc': {
                    'message': null,
                    'enabled': true
                },
                'daily_budget': {
                    'message': null,
                    'enabled': true
                }
            },
            cost: 0,
            cpc: 0,
            status: 'Active',
            status_setting: 1,
            last_synecd: (new Date()).toISOString(),
            impressions: 0,
            ctr: 0,
            daily_budget: '0',
            _demo_new: true
        };
        return angular.extend(obj, values);
    },
    contentAds: function (ids) {
        return {
            'notifications': {},
            'pagination': {
                'numPages': 1, 'count': 5, 'endIndex': 5,
                'startIndex': 1, 'currentPage': 1, 'size': 5
            },
            'lastChange': true,
            'rows': [
                {
                    'status_setting': 1,
                    'cpc': 0, 'clicks': 0, 'cost': 0, 'impressions': 0, 'ctr': 0,
                    'id': ids[0],
                    'image_urls': {
                        'square': 'http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/t/552d02c9e4b0c23003302aae/1429013198329/?format=1500w',
                        'landscape': 'http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/t/552d02c9e4b0c23003302aae/1429013198329/?format=1500w'
                    },
                    'submission_status': [
                        {'status': 2, 'text': 'Approved / Enabled', 'name': 'AdsNative'},
                        {'status': 2, 'text': 'Approved / Enabled', 'name': 'Yieldmo'}
                    ],
                    'display_url': '',
                    'url': 'http://www.zemanta.com/news/weve-partnered-with-adsnative-for-programmatic-native-supply',
                    'title': 'We’ve Partnered with AdsNative for Programmatic Native Supply',
                    'editable_fields': {'status_setting': {message: null, enabled: true}}
                },
                {
                    'status_setting': 1,
                    'cpc': 0, 'clicks': 0, 'cost': 0, 'impressions': 0, 'ctr': 0,
                    'id': ids[1],
                    'image_urls': {
                        'square': 'http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/t/552d02c9e4b0c23003302aae/1429013198329/?format=1500w',
                        'landscape': 'http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/t/552d02c9e4b0c23003302aae/1429013198329/?format=1500w'
                    },
                    'submission_status': [
                        {'status': 2, 'text': 'Approved / Enabled', 'name': 'AdsNative'},
                        {'status': 2, 'text': 'Approved / Enabled', 'name': 'Yieldmo'}
                    ],
                    'display_url': '',
                    'url': 'http://www.zemanta.com/news/weve-partnered-with-adsnative-for-programmatic-native-supply',
                    'title': 'Zemanta + AdsNative = More Native Supply Accessible Programmatically',
                    'editable_fields': {'status_setting': {message: null, enabled: true}}
                },
                {
                    'status_setting': 1,
                    'cpc': 0, 'clicks': 0, 'cost': 0, 'impressions': 0, 'ctr': 0,
                    'id': ids[2],
                    'image_urls': {
                        'square': 'http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/54369edee4b001842e669258/552d0296e4b0bfddbb2581b4/1429859532791/',
                        'landscape': 'http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/54369edee4b001842e669258/552d0296e4b0bfddbb2581b4/1429859532791/'
                    },
                    'submission_status': [
                        {'status': 2, 'text': 'Approved / Enabled', 'name': 'AdsNative'},
                        {'status': 2, 'text': 'Approved / Enabled', 'name': 'Yieldmo'}
                    ],
                    'display_url': '',
                    'url': 'http://www.zemanta.com/news/weve-partnered-with-adsnative-for-programmatic-native-supply',
                    'title': 'We’ve Partnered with AdsNative for Programmatic Native Supply',
                    'editable_fields': {'status_setting': {message: null, enabled: true}}
                },
                {
                    'status_setting': 1,
                    'cpc': 0, 'clicks': 0, 'cost': 0, 'impressions': 0, 'ctr': 0,
                    'id': ids[3],
                    'image_urls': {
                        'square': 'http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/54369edee4b001842e669258/552d0296e4b0bfddbb2581b4/1429859532791/',
                        'landscape': 'http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/54369edee4b001842e669258/552d0296e4b0bfddbb2581b4/1429859532791/'
                    },
                    'submission_status': [
                        {'status': 2, 'text': 'Approved / Enabled', 'name': 'AdsNative'},
                        {'status': 2, 'text': 'Approved / Enabled', 'name': 'Yieldmo'}
                    ],
                    'display_url': '',
                    'url': 'http://www.zemanta.com/news/weve-partnered-with-adsnative-for-programmatic-native-supply',
                    'title': 'Zemanta + AdsNative = More Native Supply Accessible Programmatically',
                    'editable_fields': {'status_setting': {message: null, enabled: true}}
                },
                {
                    'status_setting': 1,
                    'cpc': 0, 'clicks': 0, 'cost': 0, 'impressions': 0, 'ctr': 0,
                    'id': ids[4],
                    'image_urls': {
                        'square': 'http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/54369edee4b001842e669258/5507fb44e4b0fb424faf40d3/1426624899137/',
                        'landscape': 'http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/54369edee4b001842e669258/5507fb44e4b0fb424faf40d3/1426624899137/'
                    },
                    'submission_status': [
                        {'status': 2, 'text': 'Approved / Enabled', 'name': 'AdsNative'},
                        {'status': 2, 'text': 'Approved / Enabled', 'name': 'Yieldmo'}
                    ],
                    'display_url': '',
                    'url': 'http://www.zemanta.com/news/native-advertising-coming-of-age-programmatic-standards-emerge',
                    'title': 'Native Advertising Coming of Age: Programmatic Standards Emerge',
                    'editable_fields': {'status_setting': {message: null, enabled: true}}
                },
                {
                    'status_setting': 1,
                    'cpc': 0, 'clicks': 0, 'cost': 0, 'impressions': 0, 'ctr': 0,
                    'id': ids[5],
                    'image_urls': {
                        'square': 'http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/54369edee4b001842e669258/5507fb44e4b0fb424faf40d3/1426624899137/',
                        'landscape': 'http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/54369edee4b001842e669258/5507fb44e4b0fb424faf40d3/1426624899137/'
                    },
                    'submission_status': [
                        {'status': 2, 'text': 'Approved / Enabled', 'name': 'AdsNative'},
                        {'status': 2, 'text': 'Approved / Enabled', 'name': 'Yieldmo'}
                    ],
                    'display_url': '',
                    'url': 'http://www.zemanta.com/news/native-advertising-coming-of-age-programmatic-standards-emerge',
                    'title': 'OpenRTB 2.3 Will Help Native Advertising To Scale',
                    'editable_fields': {'status_setting': {message: null, enabled: true}}
                },
                {
                    'status_setting': 1,
                    'cpc': 0, 'clicks': 0, 'cost': 0, 'impressions': 0, 'ctr': 0,
                    'id': ids[6],
                    'image_urls': {
                        'square': 'http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/t/5500629de4b05b6c406ac30a/1426088613779/',
                        'landscape': 'http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/t/5500629de4b05b6c406ac30a/1426088613779/'
                    },
                    'submission_status': [
                        {'status': 2, 'text': 'Approved / Enabled', 'name': 'AdsNative'},
                        {'status': 2, 'text': 'Approved / Enabled', 'name': 'Yieldmo'}
                    ],
                    'display_url': '',
                    'url': 'http://www.zemanta.com/news/native-advertising-coming-of-age-programmatic-standards-emerge',
                    'title': 'Native Advertising Coming of Age: Programmatic Standards Emerge',
                    'editable_fields': {'status_setting': {message: null, enabled: true}}
                },
                {
                    'status_setting': 1,
                    'cpc': 0, 'clicks': 0, 'cost': 0, 'impressions': 0, 'ctr': 0,
                    'id': ids[7],
                    'image_urls': {
                        'square': 'http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/t/5500629de4b05b6c406ac30a/1426088613779/',
                        'landscape': 'http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/t/5500629de4b05b6c406ac30a/1426088613779/'
                    },
                    'submission_status': [
                        {'status': 2, 'text': 'Approved / Enabled', 'name': 'AdsNative'},
                        {'status': 2, 'text': 'Approved / Enabled', 'name': 'Yieldmo'}
                    ],
                    'display_url': '',
                    'url': 'http://www.zemanta.com/news/native-advertising-coming-of-age-programmatic-standards-emerge',
                    'title': 'OpenRTB 2.3 Will Help Native Advertising To Scale',
                    'editable_fields': {'status_setting': {message: null, enabled: true}}
                }
            ],
            'order': 'url',
            'totals': { 'impressions': 0, 'cost': 0, 'clicks': 0, 'ctr': 0, 'cpc': 0}
        };
    },
    contentAdsUpdates: {
        'notifications': {}, 'in_progress': false, 'rows': {}, 'last_change': null
    },
    tableColumns: {
        adGroupAdsPlus: ['ad_selected', 'image_urls', 'status_setting', 'submission_status', undefined, 'titleLink', 'urlLink', 'cost', 'cpc', 'clicks', 'impressions', 'ctr'],
        adGroupSources: ['checked', 'status_setting', 'name', 'status', 'bid_cpc', 'daily_budget', 'cost', 'cpc', 'clicks', 'impressions', 'ctr', 'visits', 'pageviews', undefined]
    }
});
