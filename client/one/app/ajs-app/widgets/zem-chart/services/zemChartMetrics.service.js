angular
    .module('one.widgets')
    .factory('zemChartMetricsService', function(
        zemPermissions,
        zemNavigationNewService,
        zemUtils
    ) {
        // eslint-disable-line max-len
        ////////////////////////////////////////////////////////////////////////////////////
        // Definitions - Metrics, Categories
        //
        var TYPE_NUMBER = 'number';
        var TYPE_CURRENCY = 'currency';
        var TYPE_TIME = 'time';

        var COSTS_CATEGORY_NAME = 'Costs';
        var TRAFFIC_CATEGORY_NAME = 'Traffic Acquisition';
        var MRC50_CATEGORY_NAME = 'Viewability';
        var MRC100_CATEGORY_NAME = 'MRC100 Viewability';
        var VAST4_CATEGORY_NAME = 'VAST4 Viewability';
        var AUDIENCE_CATEGORY_NAME = 'Audience Metrics';
        var VIDEO_CATEGORY_NAME = 'Video Metrics';
        var CONVERSIONS_CATEGORY_NAME = 'Google & Adobe Analytics Goals';
        var PIXELS_CATEGORY_NAME = 'Conversions & CPAs';

        var METRICS = {
            /* eslint-disable max-len */
            CLICKS: {
                name: 'Clicks',
                value: 'clicks',
                type: TYPE_NUMBER,
                shown: true,
            },
            IMPRESSIONS: {
                name: 'Impressions',
                value: 'impressions',
                type: TYPE_NUMBER,
                shown: true,
            },
            CTR: {
                name: 'CTR',
                value: 'ctr',
                type: 'percent',
                fractionSize: 2,
                shown: true,
            },

            CPC: {
                name: 'Avg. CPC',
                value: 'cpc',
                type: TYPE_CURRENCY,
                fractionSize: 3,
                costMode: constants.costMode.LEGACY,
                shown: true,
            },
            ET_CPC: {
                name: 'Avg. Platform CPC',
                value: 'et_cpc',
                type: TYPE_CURRENCY,
                fractionSize: 3,
                shown: 'zemauth.can_view_platform_cost_breakdown_derived',
                costMode: constants.costMode.PLATFORM,
                fieldGroup: 'cpc',
            },
            ETFM_CPC: {
                name: 'Avg. CPC',
                value: 'etfm_cpc',
                type: TYPE_CURRENCY,
                fractionSize: 3,
                shown: 'zemauth.can_view_end_user_cost_breakdown',
                costMode: constants.costMode.PUBLIC,
                fieldGroup: 'cpc',
            },

            CPM: {
                name: 'Avg. CPM',
                value: 'cpm',
                type: TYPE_CURRENCY,
                fractionSize: 3,
                costMode: constants.costMode.LEGACY,
                shown: true,
            },
            ET_CPM: {
                name: 'Avg. Platform CPM',
                value: 'et_cpm',
                type: TYPE_CURRENCY,
                fractionSize: 3,
                shown: 'zemauth.can_view_platform_cost_breakdown_derived',
                costMode: constants.costMode.PLATFORM,
                fieldGroup: 'cpm',
            },
            ETFM_CPM: {
                name: 'Avg. CPM',
                value: 'etfm_cpm',
                type: TYPE_CURRENCY,
                fractionSize: 3,
                shown: 'zemauth.can_view_end_user_cost_breakdown',
                costMode: constants.costMode.PUBLIC,
                fieldGroup: 'cpm',
            },

            DATA_COST: {
                name: 'Actual Data Cost',
                value: 'data_cost',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                shown: 'zemauth.can_view_actual_costs',
            },
            MEDIA_COST: {
                name: 'Actual Media Spend',
                value: 'media_cost',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                shown: 'zemauth.can_view_actual_costs',
            },
            E_DATA_COST: {
                name: 'Data Cost',
                value: 'e_data_cost',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                shown: 'zemauth.can_view_platform_cost_breakdown',
            },
            E_MEDIA_COST: {
                name: 'Media Spend',
                value: 'e_media_cost',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                shown: 'zemauth.can_view_platform_cost_breakdown',
            },

            BILLING_COST: {
                name: 'Total Spend',
                value: 'billing_cost',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                costMode: constants.costMode.LEGACY,
                shown: true,
            },

            ETFM_COST: {
                name: 'Total Spend',
                value: 'etfm_cost',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                shown: 'zemauth.can_view_end_user_cost_breakdown',
                costMode: constants.costMode.ANY,
            },
            ETF_COST: {
                name: 'Agency Spend',
                value: 'etf_cost',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                shown: 'zemauth.can_view_agency_cost_breakdown',
                costMode: constants.costMode.ANY,
            },
            ET_COST: {
                name: 'Platform Spend',
                value: 'et_cost',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                shown: 'zemauth.can_view_platform_cost_breakdown_derived',
                costMode: constants.costMode.ANY,
            },

            LICENSE_FEE: {
                name: 'License Fee',
                value: 'license_fee',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                shown: 'zemauth.can_view_platform_cost_breakdown',
            },

            VISITS: {
                name: 'Visits',
                value: 'visits',
                type: TYPE_NUMBER,
                shown: true,
            },
            PAGEVIEWS: {
                name: 'Pageviews',
                value: 'pageviews',
                type: TYPE_NUMBER,
                shown: true,
            },
            CLICK_DISCREPANCY: {
                name: 'Click Discrepancy',
                value: 'click_discrepancy',
                type: 'percent',
                fractionSize: 2,
                shown: 'zemauth.aggregate_postclick_acquisition',
            },
            PERCENT_NEW_USERS: {
                name: '% New Users',
                value: 'percent_new_users',
                type: 'percent',
                fractionSize: 2,
                shown: true,
            },
            RETURNING_USERS: {
                name: 'Returning Users',
                value: 'returning_users',
                type: TYPE_NUMBER,
                shown: true,
            },
            UNIQUE_USERS: {
                name: 'Unique Users',
                value: 'unique_users',
                type: TYPE_NUMBER,
                shown: true,
            },
            NEW_USERS: {
                name: 'New Users',
                value: 'new_users',
                type: TYPE_NUMBER,
                shown: true,
            },
            BOUNCE_RATE: {
                name: 'Bounce Rate',
                value: 'bounce_rate',
                type: 'percent',
                fractionSize: 2,
                shown: true,
            },
            TOTAL_SECONDS: {
                name: 'Total Seconds',
                value: 'total_seconds',
                type: TYPE_NUMBER,
                shown: true,
            },
            BOUNCED_VISITS: {
                name: 'Bounced Visits',
                value: 'bounced_visits',
                type: TYPE_NUMBER,
                shown: true,
            },
            NON_BOUNCED_VISITS: {
                name: 'Non-Bounced Visits',
                value: 'non_bounced_visits',
                type: TYPE_NUMBER,
                shown: true,
            },
            PV_PER_VISIT: {
                name: 'Pageviews per Visit',
                value: 'pv_per_visit',
                type: TYPE_NUMBER,
                fractionSize: 2,
                shown: true,
            },
            AVG_TOS: {
                name: 'Time on Site',
                value: 'avg_tos',
                type: TYPE_TIME,
                fractionSize: 1,
                shown: true,
            },

            COST_PER_MINUTE: {
                name: 'Avg. Cost per Minute',
                value: 'avg_cost_per_minute',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                costMode: constants.costMode.LEGACY,
                shown: true,
            },
            COST_PER_PAGEVIEW: {
                name: 'Avg. Cost for Pageview',
                value: 'avg_cost_per_pageview',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                costMode: constants.costMode.LEGACY,
                shown: true,
            },
            COST_PER_VISIT: {
                name: 'Avg. Cost per Visit',
                value: 'avg_cost_per_visit',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                costMode: constants.costMode.LEGACY,
                shown: true,
            },
            COST_PER_NON_BOUNCED_VISIT: {
                name: 'Avg. Cost per Non-Bounced Visit',
                value: 'avg_cost_per_non_bounced_visit',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                costMode: constants.costMode.LEGACY,
                shown: true,
            },
            COST_PER_NEW_VISITOR: {
                name: 'Avg. Cost for New Visitor',
                value: 'avg_cost_for_new_visitor',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                costMode: constants.costMode.LEGACY,
                shown: true,
            },

            ET_COST_PER_MINUTE: {
                name: 'Avg. Platform Cost per Minute',
                value: 'avg_et_cost_per_minute',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                costMode: constants.costMode.PLATFORM,
                shown: 'zemauth.can_view_platform_cost_breakdown_derived',
                fieldGroup: 'avg_cost_per_minute',
            },
            ETFM_COST_PER_MINUTE: {
                name: 'Avg. Cost per Minute',
                value: 'avg_etfm_cost_per_minute',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                costMode: constants.costMode.PUBLIC,
                shown: 'zemauth.can_view_end_user_cost_breakdown',
                fieldGroup: 'avg_cost_per_minute',
            },
            ET_COST_PER_PAGEVIEW: {
                name: 'Avg. Platform Cost for Pageview',
                value: 'avg_et_cost_per_pageview',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                costMode: constants.costMode.PLATFORM,
                shown: 'zemauth.can_view_platform_cost_breakdown_derived',
                fieldGroup: 'avg_cost_per_pageview',
            },
            ETFM_COST_PER_PAGEVIEW: {
                name: 'Avg. Cost for Pageview',
                value: 'avg_etfm_cost_per_pageview',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                costMode: constants.costMode.PUBLIC,
                shown: 'zemauth.can_view_end_user_cost_breakdown',
                fieldGroup: 'avg_cost_per_pageview',
            },
            ET_COST_PER_VISIT: {
                name: 'Avg. Platform Cost per Visit',
                value: 'avg_et_cost_per_visit',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                costMode: constants.costMode.PLATFORM,
                shown: 'zemauth.can_view_platform_cost_breakdown_derived',
                fieldGroup: 'avg_cost_per_visit',
            },
            ETFM_COST_PER_VISIT: {
                name: 'Avg. Cost per Visit',
                value: 'avg_etfm_cost_per_visit',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                costMode: constants.costMode.PUBLIC,
                shown: 'zemauth.can_view_end_user_cost_breakdown',
                fieldGroup: 'avg_cost_per_visit',
            },
            ET_COST_PER_NON_BOUNCED_VISIT: {
                name: 'Avg. Platform Cost per Non-Bounced Visit',
                value: 'avg_et_cost_per_non_bounced_visit',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                costMode: constants.costMode.PLATFORM,
                shown: 'zemauth.can_view_platform_cost_breakdown_derived',
                fieldGroup: 'avg_cost_per_non_bounced_visit',
            },
            ETFM_COST_PER_NON_BOUNCED_VISIT: {
                name: 'Avg. Cost per Non-Bounced Visit',
                value: 'avg_etfm_cost_per_non_bounced_visit',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                costMode: constants.costMode.PUBLIC,
                shown: 'zemauth.can_view_end_user_cost_breakdown',
                fieldGroup: 'avg_cost_per_non_bounced_visit',
            },
            ET_COST_PER_NEW_VISITOR: {
                name: 'Avg. Platform Cost for New Visitor',
                value: 'avg_et_cost_for_new_visitor',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                costMode: constants.costMode.PLATFORM,
                shown: 'zemauth.can_view_platform_cost_breakdown_derived',
                fieldGroup: 'avg_cost_for_new_visitor',
            },
            ETFM_COST_PER_NEW_VISITOR: {
                name: 'Avg. Cost for New Visitor',
                value: 'avg_etfm_cost_for_new_visitor',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                costMode: constants.costMode.PUBLIC,
                shown: 'zemauth.can_view_end_user_cost_breakdown',
                fieldGroup: 'avg_cost_for_new_visitor',
            },

            VIDEO_START: {
                name: 'Video Start',
                value: 'video_start',
                type: TYPE_NUMBER,
                shown: 'zemauth.fea_can_see_video_metrics',
            },
            VIDEO_PROGRESS_3S: {
                name: 'Video Progress 3s',
                value: 'video_progress_3s',
                type: TYPE_NUMBER,
                shown: 'zemauth.fea_can_see_video_metrics',
            },
            VIDEO_FIRST_QUARTILE: {
                name: 'Video First Quartile',
                value: 'video_first_quartile',
                type: TYPE_NUMBER,
                shown: 'zemauth.fea_can_see_video_metrics',
            },
            VIDEO_MIDPOINT: {
                name: 'Video Midpoint',
                value: 'video_midpoint',
                type: TYPE_NUMBER,
                shown: 'zemauth.fea_can_see_video_metrics',
            },
            VIDEO_THIRD_QUARTILE: {
                name: 'Video Third Quartile',
                value: 'video_third_quartile',
                type: TYPE_NUMBER,
                shown: 'zemauth.fea_can_see_video_metrics',
            },
            VIDEO_COMPLETE: {
                name: 'Video Complete',
                value: 'video_complete',
                type: TYPE_NUMBER,
                shown: 'zemauth.fea_can_see_video_metrics',
            },

            VIDEO_CPV: {
                name: 'Avg. CPV',
                value: 'video_cpv',
                type: TYPE_CURRENCY,
                fractionSize: 3,
                shown: 'zemauth.fea_can_see_video_metrics',
                costMode: constants.costMode.LEGACY,
                internal: 'zemauth.fea_can_see_video_metrics',
            },
            VIDEO_ET_CPV: {
                name: 'Avg. Platform CPV',
                value: 'video_et_cpv',
                type: TYPE_CURRENCY,
                fractionSize: 3,
                shown: [
                    'zemauth.fea_can_see_video_metrics',
                    'zemauth.can_view_platform_cost_breakdown_derived',
                ],
                costMode: constants.costMode.PLATFORM,
                internal: 'zemauth.fea_can_see_video_metrics',
                fieldGroup: 'video_cpv',
            },
            VIDEO_ETFM_CPV: {
                name: 'Avg. CPV',
                value: 'video_etfm_cpv',
                type: TYPE_CURRENCY,
                fractionSize: 3,
                shown: [
                    'zemauth.fea_can_see_video_metrics',
                    'zemauth.can_view_end_user_cost_breakdown',
                ],
                costMode: constants.costMode.PUBLIC,
                internal: 'zemauth.fea_can_see_video_metrics',
                fieldGroup: 'video_cpv',
            },
            VIDEO_CPCV: {
                name: 'Avg. CPCV',
                value: 'video_cpcv',
                type: TYPE_CURRENCY,
                fractionSize: 3,
                shown: 'zemauth.fea_can_see_video_metrics',
                costMode: constants.costMode.LEGACY,
                internal: 'zemauth.fea_can_see_video_metrics',
            },
            VIDEO_ET_CPCV: {
                name: 'Avg. Platform CPCV',
                value: 'video_et_cpcv',
                type: TYPE_CURRENCY,
                fractionSize: 3,
                shown: [
                    'zemauth.fea_can_see_video_metrics',
                    'zemauth.can_view_platform_cost_breakdown_derived',
                ],
                costMode: constants.costMode.PLATFORM,
                internal: 'zemauth.fea_can_see_video_metrics',
                fieldGroup: 'video_cpcv',
            },
            VIDEO_ETFM_CPCV: {
                name: 'Avg. CPCV',
                value: 'video_etfm_cpcv',
                type: TYPE_CURRENCY,
                fractionSize: 3,
                shown: [
                    'zemauth.fea_can_see_video_metrics',
                    'zemauth.can_view_end_user_cost_breakdown',
                ],
                costMode: constants.costMode.PUBLIC,
                internal: 'zemauth.fea_can_see_video_metrics',
                fieldGroup: 'video_cpcv',
            },
            MRC50_MEASURABLE: {
                name: 'Measurable Impressions',
                value: 'mrc50_measurable',
                type: TYPE_NUMBER,
                shown: ['zemauth.can_see_mrc50_metrics'],
                shortName: 'Measurable',
            },
            MRC50_VIEWABLE: {
                name: 'Viewable Impressions',
                value: 'mrc50_viewable',
                type: TYPE_NUMBER,
                shown: ['zemauth.can_see_mrc50_metrics'],
                shortName: 'Viewable',
            },
            MRC50_NON_MEASURABLE: {
                name: 'Not-Measurable Impressions',
                value: 'mrc50_non_measurable',
                type: TYPE_NUMBER,
                shown: ['zemauth.can_see_mrc50_metrics'],
                shortName: 'Not-Measurable',
            },
            MRC50_NON_VIEWABLE: {
                name: 'Not-Viewable Impressions',
                value: 'mrc50_non_viewable',
                type: TYPE_NUMBER,
                shown: ['zemauth.can_see_mrc50_metrics'],
                shortName: 'Not-Viewable',
            },
            MRC50_MEASURABLE_PERCENT: {
                name: '% Measurable Impressions',
                value: 'mrc50_measurable_percent',
                type: 'percent',
                fractionSize: 2,
                shown: ['zemauth.can_see_mrc50_metrics'],
                shortName: '% Measurable',
            },
            MRC50_VIEWABLE_PERCENT: {
                name: '% Viewable Impressions',
                value: 'mrc50_viewable_percent',
                type: 'percent',
                fractionSize: 2,
                shown: ['zemauth.can_see_mrc50_metrics'],
                shortName: '% Viewable',
            },
            MRC50_VIEWABLE_DISTRIBUTION: {
                name: 'Impression Distribution (Viewable)',
                value: 'mrc50_viewable_distribution',
                type: 'percent',
                fractionSize: 2,
                shown: ['zemauth.can_see_mrc50_metrics'],
                shortName: 'Viewable Dist.',
            },
            MRC50_NON_MEASURABLE_DISTRIBUTION: {
                name: 'Impression Distribution (Not-Measurable)',
                value: 'mrc50_non_measurable_distribution',
                type: 'percent',
                fractionSize: 2,
                shown: ['zemauth.can_see_mrc50_metrics'],
                shortName: 'Non-Measurable Dist.',
            },
            MRC50_NON_VIEWABLE_DISTRIBUTION: {
                name: 'Impression Distribution (Not-Viewable)',
                value: 'mrc50_non_viewable_distribution',
                type: 'percent',
                fractionSize: 2,
                shown: ['zemauth.can_see_mrc50_metrics'],
                shortName: 'Non-Viewable Dist.',
            },
            ET_MRC50_VCPM: {
                name: 'Avg. Platform VCPM',
                value: 'et_mrc50_vcpm',
                type: TYPE_CURRENCY,
                fractionSize: 3,
                shown: ['zemauth.can_see_mrc50_metrics'],
                costMode: constants.costMode.PLATFORM,
                fieldGroup: 'mrc50_vcpm',
                shortName: 'Avg. Platform VCPM',
            },
            ETFM_MRC50_VCPM: {
                name: 'Avg. VCPM',
                value: 'etfm_mrc50_vcpm',
                type: TYPE_CURRENCY,
                fractionSize: 3,
                shown: ['zemauth.can_see_mrc50_metrics'],
                costMode: constants.costMode.PUBLIC,
                fieldGroup: 'mrc50_vcpm',
                shortName: 'Avg. VCPM',
            },
            MRC100_MEASURABLE: {
                name: 'MRC100 Measurable Impressions',
                value: 'mrc100_measurable',
                type: TYPE_NUMBER,
                shown: ['zemauth.can_see_mrc100_metrics'],
                internal: 'zemauth.can_see_mrc100_metrics',
                shortName: 'Measurable',
            },
            MRC100_VIEWABLE: {
                name: 'MRC100 Viewable Impressions',
                value: 'mrc100_viewable',
                type: TYPE_NUMBER,
                shown: ['zemauth.can_see_mrc100_metrics'],
                internal: 'zemauth.can_see_mrc100_metrics',
                shortName: 'Viewable',
            },
            MRC100_NON_MEASURABLE: {
                name: 'MRC100 Not-Measurable Impressions',
                value: 'mrc100_non_measurable',
                type: TYPE_NUMBER,
                shown: ['zemauth.can_see_mrc100_metrics'],
                internal: 'zemauth.can_see_mrc100_metrics',
                shortName: 'Not-Measurable',
            },
            MRC100_NON_VIEWABLE: {
                name: 'MRC100 Not-Viewable Impressions',
                value: 'mrc100_non_viewable',
                type: TYPE_NUMBER,
                shown: ['zemauth.can_see_mrc100_metrics'],
                internal: 'zemauth.can_see_mrc100_metrics',
                shortName: 'Not-Viewable',
            },
            MRC100_MEASURABLE_PERCENT: {
                name: '% MRC100 Measurable Impressions',
                value: 'mrc100_measurable_percent',
                type: 'percent',
                fractionSize: 2,
                shown: ['zemauth.can_see_mrc100_metrics'],
                internal: 'zemauth.can_see_mrc100_metrics',
                shortName: '% Measurable',
            },
            MRC100_VIEWABLE_PERCENT: {
                name: '% MRC100 Viewable Impressions',
                value: 'mrc100_viewable_percent',
                type: 'percent',
                fractionSize: 2,
                shown: ['zemauth.can_see_mrc100_metrics'],
                internal: 'zemauth.can_see_mrc100_metrics',
                shortName: '% Viewable',
            },
            MRC100_VIEWABLE_DISTRIBUTION: {
                name: 'MRC100 Impression Distribution (Viewable)',
                value: 'mrc100_viewable_distribution',
                type: 'percent',
                fractionSize: 2,
                shown: ['zemauth.can_see_mrc100_metrics'],
                internal: 'zemauth.can_see_mrc100_metrics',
                shortName: 'Viewable Dist.',
            },
            MRC100_NON_MEASURABLE_DISTRIBUTION: {
                name: 'MRC100 Impression Distribution (Not-Measurable)',
                value: 'mrc100_non_measurable_distribution',
                type: 'percent',
                fractionSize: 2,
                shown: ['zemauth.can_see_mrc100_metrics'],
                internal: 'zemauth.can_see_mrc100_metrics',
                shortName: 'Non-Measurable Dist.',
            },
            MRC100_NON_VIEWABLE_DISTRIBUTION: {
                name: 'MRC100 Impression Distribution (Not-Viewable)',
                value: 'mrc100_non_viewable_distribution',
                type: 'percent',
                fractionSize: 2,
                shown: ['zemauth.can_see_mrc100_metrics'],
                internal: 'zemauth.can_see_mrc100_metrics',
                shortName: 'Non-Viewable Dist.',
            },
            ET_MRC100_VCPM: {
                name: 'Avg. MRC100 Platform VCPM',
                value: 'et_mrc100_vcpm',
                type: TYPE_CURRENCY,
                fractionSize: 3,
                shown: ['zemauth.can_see_mrc100_metrics'],
                costMode: constants.costMode.PLATFORM,
                internal: 'zemauth.can_see_mrc100_metrics',
                fieldGroup: 'mrc100_vcpm',
                shortName: 'Avg. Platform VCPM',
            },
            ETFM_MRC100_VCPM: {
                name: 'Avg. MRC100 VCPM',
                value: 'etfm_mrc100_vcpm',
                type: TYPE_CURRENCY,
                fractionSize: 3,
                shown: ['zemauth.can_see_mrc100_metrics'],
                costMode: constants.costMode.PUBLIC,
                internal: 'zemauth.can_see_mrc100_metrics',
                fieldGroup: 'mrc100_vcpm',
                shortName: 'Avg. VCPM',
            },
            VAST4_MEASURABLE: {
                name: 'VAST4 Measurable Impressions',
                value: 'vast4_measurable',
                type: TYPE_NUMBER,
                shown: ['zemauth.can_see_vast4_metrics'],
                internal: 'zemauth.can_see_vast4_metrics',
                shortName: 'Measurable',
            },
            VAST4_VIEWABLE: {
                name: 'VAST4 Viewable Impressions',
                value: 'vast4_viewable',
                type: TYPE_NUMBER,
                shown: ['zemauth.can_see_vast4_metrics'],
                internal: 'zemauth.can_see_vast4_metrics',
                shortName: 'Viewable',
            },
            VAST4_NON_MEASURABLE: {
                name: 'VAST4 Non-Measurable',
                value: 'vast4_non_measurable',
                type: TYPE_NUMBER,
                shown: ['zemauth.can_see_vast4_metrics'],
                internal: 'zemauth.can_see_vast4_metrics',
                shortName: 'Not-Measurable',
            },
            VAST4_NON_VIEWABLE: {
                name: 'VAST4 Non-Viewable',
                value: 'vast4_non_viewable',
                type: TYPE_NUMBER,
                shown: ['zemauth.can_see_vast4_metrics'],
                internal: 'zemauth.can_see_vast4_metrics',
                shortName: 'Not-Viewable',
            },
            VAST4_MEASURABLE_PERCENT: {
                name: '% VAST4 Measurable Impressions',
                value: 'vast4_measurable_percent',
                type: 'percent',
                fractionSize: 2,
                shown: ['zemauth.can_see_vast4_metrics'],
                internal: 'zemauth.can_see_vast4_metrics',
                shortName: '% Measurable',
            },
            VAST4_VIEWABLE_PERCENT: {
                name: '% VAST4 Viewable Impressions',
                value: 'vast4_viewable_percent',
                type: 'percent',
                fractionSize: 2,
                shown: ['zemauth.can_see_vast4_metrics'],
                internal: 'zemauth.can_see_vast4_metrics',
                shortName: '% Viewable',
            },
            VAST4_VIEWABLE_DISTRIBUTION: {
                name: 'VAST4 Impression Distribution (Viewable)',
                value: 'vast4_viewable_distribution',
                type: 'percent',
                fractionSize: 2,
                shown: ['zemauth.can_see_vast4_metrics'],
                internal: 'zemauth.can_see_vast4_metrics',
                shortName: 'Viewable Dist.',
            },
            VAST4_NON_MEASURABLE_DISTRIBUTION: {
                name: 'VAST4 Impression Distribution (Not-Measurable)',
                value: 'vast4_non_measurable_distribution',
                type: 'percent',
                fractionSize: 2,
                shown: ['zemauth.can_see_vast4_metrics'],
                internal: 'zemauth.can_see_vast4_metrics',
                shortName: 'Non-Measurable Dist.',
            },
            VAST4_NON_VIEWABLE_DISTRIBUTION: {
                name: 'VAST4 Impression Distribution (Not-Viewable)',
                value: 'vast4_non_viewable_distribution',
                type: 'percent',
                fractionSize: 2,
                shown: ['zemauth.can_see_vast4_metrics'],
                internal: 'zemauth.can_see_vast4_metrics',
                shortName: 'Non-Viewable Dist.',
            },
            ET_VAST4_VCPM: {
                name: 'Avg. VAST4 Platform VCPM',
                value: 'et_vast4_vcpm',
                type: TYPE_CURRENCY,
                fractionSize: 3,
                shown: ['zemauth.can_see_vast4_metrics'],
                costMode: constants.costMode.PLATFORM,
                internal: 'zemauth.can_see_vast4_metrics',
                fieldGroup: 'vast4_vcpm',
                shortName: 'Avg. Platform VCPM',
            },
            ETFM_VAST4_VCPM: {
                name: 'Avg. VAST4 VCPM',
                value: 'etfm_vast4_vcpm',
                type: TYPE_CURRENCY,
                fractionSize: 3,
                shown: ['zemauth.can_see_vast4_metrics'],
                costMode: constants.costMode.PUBLIC,
                internal: 'zemauth.can_see_vast4_metrics',
                fieldGroup: 'vast4_vcpm',
                shortName: 'Avg. VCPM',
            },
        };
        /* eslint-enable max-len */

        var TRAFFIC_ACQUISITION = [
            METRICS.IMPRESSIONS,
            METRICS.CLICKS,
            METRICS.CTR,
            METRICS.CPC,
            METRICS.ET_CPC,
            METRICS.ETFM_CPC,
            METRICS.CPM,
            METRICS.ET_CPM,
            METRICS.ETFM_CPM,
        ];

        var MRC50_VIEWABILITY_METRICS = [
            METRICS.MRC50_MEASURABLE,
            METRICS.MRC50_VIEWABLE,
            METRICS.MRC50_NON_MEASURABLE,
            METRICS.MRC50_NON_VIEWABLE,
            METRICS.MRC50_MEASURABLE_PERCENT,
            METRICS.MRC50_VIEWABLE_PERCENT,
            METRICS.MRC50_VIEWABLE_DISTRIBUTION,
            METRICS.MRC50_NON_MEASURABLE_DISTRIBUTION,
            METRICS.MRC50_NON_VIEWABLE_DISTRIBUTION,
            METRICS.ET_MRC50_VCPM,
            METRICS.ETFM_MRC50_VCPM,
        ];

        var MRC100_VIEWABILITY_METRICS = [
            METRICS.MRC100_MEASURABLE,
            METRICS.MRC100_VIEWABLE,
            METRICS.MRC100_NON_MEASURABLE,
            METRICS.MRC100_NON_VIEWABLE,
            METRICS.MRC100_MEASURABLE_PERCENT,
            METRICS.MRC100_VIEWABLE_PERCENT,
            METRICS.MRC100_VIEWABLE_DISTRIBUTION,
            METRICS.MRC100_NON_MEASURABLE_DISTRIBUTION,
            METRICS.MRC100_NON_VIEWABLE_DISTRIBUTION,
            METRICS.ET_MRC100_VCPM,
            METRICS.ETFM_MRC100_VCPM,
        ];

        var VAST4_VIEWABILITY_METRICS = [
            METRICS.VAST4_MEASURABLE,
            METRICS.VAST4_VIEWABLE,
            METRICS.VAST4_NON_MEASURABLE,
            METRICS.VAST4_NON_VIEWABLE,
            METRICS.VAST4_MEASURABLE_PERCENT,
            METRICS.VAST4_VIEWABLE_PERCENT,
            METRICS.VAST4_VIEWABLE_DISTRIBUTION,
            METRICS.VAST4_NON_MEASURABLE_DISTRIBUTION,
            METRICS.VAST4_NON_VIEWABLE_DISTRIBUTION,
            METRICS.ET_VAST4_VCPM,
            METRICS.ETFM_VAST4_VCPM,
        ];

        var COST_METRICS = [
            METRICS.MEDIA_COST,
            METRICS.E_MEDIA_COST,
            METRICS.DATA_COST,
            METRICS.E_DATA_COST,
            METRICS.LICENSE_FEE,
            METRICS.BILLING_COST,
            METRICS.ETFM_COST,
            METRICS.ETF_COST,
            METRICS.ET_COST,
        ];

        var POST_CLICK_METRICS = [
            METRICS.VISITS,
            METRICS.UNIQUE_USERS,
            METRICS.NEW_USERS,
            METRICS.RETURNING_USERS,
            METRICS.PERCENT_NEW_USERS,
            METRICS.CLICK_DISCREPANCY,
            METRICS.PAGEVIEWS,
            METRICS.PV_PER_VISIT,
            METRICS.BOUNCED_VISITS,
            METRICS.NON_BOUNCED_VISITS,
            METRICS.BOUNCE_RATE,
            METRICS.TOTAL_SECONDS,
            METRICS.AVG_TOS,
        ];

        var GOAL_METRICS = [
            METRICS.COST_PER_VISIT,
            METRICS.ET_COST_PER_VISIT,
            METRICS.ETFM_COST_PER_VISIT,
            METRICS.COST_PER_NEW_VISITOR,
            METRICS.ET_COST_PER_NEW_VISITOR,
            METRICS.ETFM_COST_PER_NEW_VISITOR,
            METRICS.COST_PER_PAGEVIEW,
            METRICS.ET_COST_PER_PAGEVIEW,
            METRICS.ETFM_COST_PER_PAGEVIEW,
            METRICS.COST_PER_NON_BOUNCED_VISIT,
            METRICS.ET_COST_PER_NON_BOUNCED_VISIT,
            METRICS.ETFM_COST_PER_NON_BOUNCED_VISIT,
            METRICS.COST_PER_MINUTE,
            METRICS.ET_COST_PER_MINUTE,
            METRICS.ETFM_COST_PER_MINUTE,
        ];

        var VIDEO_METRICS = [
            METRICS.VIDEO_START,
            METRICS.VIDEO_PROGRESS_3S,
            METRICS.VIDEO_FIRST_QUARTILE,
            METRICS.VIDEO_MIDPOINT,
            METRICS.VIDEO_THIRD_QUARTILE,
            METRICS.VIDEO_COMPLETE,
            METRICS.VIDEO_CPV,
            METRICS.VIDEO_ET_CPV,
            METRICS.VIDEO_ETFM_CPV,
            METRICS.VIDEO_CPCV,
            METRICS.VIDEO_ET_CPCV,
            METRICS.VIDEO_ETFM_CPCV,
        ];

        var AUDIENCE_METRICS = [].concat(POST_CLICK_METRICS, GOAL_METRICS);

        ////////////////////////////////////////////////////////////////////////////////////
        // Service functions
        //
        function getChartMetrics() {
            var categories = [];
            categories.push({
                name: COSTS_CATEGORY_NAME,
                metrics: createMetrics(COST_METRICS),
            });
            categories.push({
                name: TRAFFIC_CATEGORY_NAME,
                metrics: createMetrics(TRAFFIC_ACQUISITION),
            });
            categories.push({
                name: MRC50_CATEGORY_NAME,
                metrics: createMetrics(MRC50_VIEWABILITY_METRICS),
                isNewFeature: true,
            });
            categories.push({
                name: MRC100_CATEGORY_NAME,
                metrics: createMetrics(MRC100_VIEWABILITY_METRICS),
                isNewFeature: true,
            });
            categories.push({
                name: VAST4_CATEGORY_NAME,
                metrics: createMetrics(VAST4_VIEWABILITY_METRICS),
                isNewFeature: true,
            });
            categories.push({
                name: AUDIENCE_CATEGORY_NAME,
                metrics: createMetrics(AUDIENCE_METRICS),
            });
            categories.push({
                name: VIDEO_CATEGORY_NAME,
                metrics: createMetrics(VIDEO_METRICS),
            });

            return categories;
        }

        function checkPermissions(metrics) {
            // Go through all the metrics and convert permissions to boolean when needed

            var usesBCMv2 = zemNavigationNewService.getUsesBCMv2();
            var newCostModes = [
                constants.costMode.PLATFORM,
                constants.costMode.PUBLIC,
                constants.costMode.ANY,
            ];
            var hasPermission = function(permission) {
                return zemPermissions.hasPermissionBCMv2(permission, usesBCMv2);
            };
            var isPermissionInternal = function(permission) {
                return zemPermissions.isPermissionInternalBCMv2(
                    permission,
                    usesBCMv2
                );
            };

            metrics.forEach(function(metric) {
                metric.internal = zemUtils.convertPermission(
                    metric.internal,
                    isPermissionInternal
                );

                var shown = zemUtils.convertPermission(
                    metric.shown,
                    hasPermission
                );
                if (shown) {
                    if (
                        usesBCMv2 &&
                        metric.costMode === constants.costMode.LEGACY
                    ) {
                        // don't show old metrics in BCMv2 accounts
                        shown = false;
                    } else if (
                        !usesBCMv2 &&
                        newCostModes.indexOf(metric.costMode) >= 0
                    ) {
                        // don't show new metrics in non-BCMv2 accounts
                        shown = false;
                    }
                }

                metric.shown = shown;
            });
        }

        function createMetrics(metricDefinitions) {
            var metrics = angular.copy(metricDefinitions);
            checkPermissions(metrics);
            return metrics.filter(function(metric) {
                return metric.shown;
            });
        }

        function insertDynamicMetrics(categories, pixels, conversionGoals) {
            if (!findCategoryByName(categories, PIXELS_CATEGORY_NAME)) {
                insertPixelCategory(categories, pixels);
            }

            if (!findCategoryByName(categories, CONVERSIONS_CATEGORY_NAME)) {
                insertConversionCategory(categories, conversionGoals);
            }
        }

        function insertPixelCategory(categories, pixels) {
            if (!pixels || pixels.length === 0) return;

            var pixelSubcategories = [];
            angular.forEach(pixels, function(pixel) {
                var pixelSubCategory = {
                    name: pixel.name,
                    metrics: [],
                    subcategories: [],
                };
                var pixelGoalSubCategory = {
                    name: 'CPA (' + pixel.name + ')',
                    metrics: [],
                    subcategories: [],
                };

                generatePixelCategories(
                    pixelSubCategory,
                    pixelGoalSubCategory,
                    pixel,
                    options.conversionWindows,
                    '',
                    zemPermissions.hasPermission(
                        'zemauth.can_see_viewthrough_conversions'
                    )
                        ? ' - Click attr.'
                        : '',
                    'Click attr.:'
                );
                if (
                    zemPermissions.hasPermission(
                        'zemauth.can_see_viewthrough_conversions'
                    )
                ) {
                    generatePixelCategories(
                        pixelSubCategory,
                        pixelGoalSubCategory,
                        pixel,
                        options.conversionWindowsViewthrough,
                        '_view',
                        ' - View attr.',
                        'View attr.:'
                    );
                }
                pixelSubcategories.push(pixelSubCategory, pixelGoalSubCategory);
            });

            categories.push({
                name: PIXELS_CATEGORY_NAME,
                description: 'Choose conversion window in days.',
                metrics: [],
                subcategories: pixelSubcategories,
            });
        }

        function generatePixelCategories(
            pixelSubCategory,
            pixelGoalSubCategory,
            pixel,
            conversionWindows,
            fieldSuffix,
            columnSuffix,
            subRowName
        ) {
            var pixelMetrics = [];
            var pixelGoalMetrics = [];

            angular.forEach(conversionWindows, function(conversionWindow) {
                var metricValue =
                    pixel.prefix + '_' + conversionWindow.value + fieldSuffix;

                pixelMetrics.push({
                    value: metricValue,
                    shortName: conversionWindow.value / 24,
                    name:
                        pixel.name + ' ' + conversionWindow.name + columnSuffix,
                    shown: true,
                });

                pixelGoalMetrics.push({
                    value: 'avg_cost_per_' + metricValue,
                    shortName: conversionWindow.value / 24,
                    name:
                        'CPA (' +
                        pixel.name +
                        ' ' +
                        conversionWindow.name +
                        columnSuffix +
                        ')',
                    type: TYPE_CURRENCY,
                    fractionSize: 2,
                    shown: true,
                    costMode: constants.costMode.LEGACY,
                });

                pixelGoalMetrics.push({
                    value: 'avg_et_cost_per_' + metricValue,
                    shortName: conversionWindow.value / 24 + '(P)',
                    name:
                        'Platform CPA (' +
                        pixel.name +
                        ' ' +
                        conversionWindow.name +
                        columnSuffix +
                        ')',
                    type: TYPE_CURRENCY,
                    fractionSize: 2,
                    shown: 'zemauth.can_view_platform_cost_breakdown_derived',
                    costMode: constants.costMode.PLATFORM,
                    fieldGroup: 'avg_cost_per_' + metricValue,
                });

                pixelGoalMetrics.push({
                    value: 'avg_etfm_cost_per_' + metricValue,
                    shortName: conversionWindow.value / 24,
                    name:
                        'CPA (' +
                        pixel.name +
                        ' ' +
                        conversionWindow.name +
                        columnSuffix +
                        ')',
                    type: TYPE_CURRENCY,
                    fractionSize: 2,
                    shown: 'zemauth.can_view_end_user_cost_breakdown',
                    costMode: constants.costMode.PUBLIC,
                    fieldGroup: 'avg_cost_per_' + metricValue,
                });
            });

            checkPermissions(pixelMetrics);
            checkPermissions(pixelGoalMetrics);

            pixelSubCategory.subcategories.push({
                name: subRowName,
                metrics: pixelMetrics.filter(function(metric) {
                    return metric.shown;
                }),
                subcategories: [],
            });

            pixelGoalSubCategory.subcategories.push({
                name: subRowName,
                metrics: pixelGoalMetrics.filter(function(metric) {
                    return metric.shown;
                }),
                subcategories: [],
            });
        }

        function insertConversionCategory(categories, conversionGoals) {
            if (!conversionGoals || conversionGoals.length === 0) return;
            var conversionMetrics = [];
            var conversionGoalMetrics = [];
            angular.forEach(conversionGoals, function(goal) {
                conversionMetrics.push({
                    value: goal.id,
                    name: goal.name,
                    shown: true,
                });

                conversionGoalMetrics.push({
                    value: 'avg_cost_per_' + goal.id,
                    name: 'CPA (' + goal.name + ')',
                    type: TYPE_CURRENCY,
                    fractionSize: 2,
                    shown: true,
                    costMode: constants.costMode.LEGACY,
                });

                conversionGoalMetrics.push({
                    value: 'avg_et_cost_per_' + goal.id,
                    name: 'Platform CPA (' + goal.name + ')',
                    type: TYPE_CURRENCY,
                    fractionSize: 2,
                    shown: 'zemauth.can_view_platform_cost_breakdown_derived',
                    costMode: constants.costMode.PLATFORM,
                    fieldGroup: 'avg_cost_per_' + goal.id,
                });

                conversionGoalMetrics.push({
                    value: 'avg_etfm_cost_per_' + goal.id,
                    name: 'CPA (' + goal.name + ')',
                    type: TYPE_CURRENCY,
                    fractionSize: 2,
                    shown: 'zemauth.can_view_end_user_cost_breakdown',
                    costMode: constants.costMode.PUBLIC,
                    fieldGroup: 'avg_cost_per_' + goal.id,
                });
            });

            checkPermissions(conversionMetrics);
            checkPermissions(conversionGoalMetrics);

            categories.push({
                name: CONVERSIONS_CATEGORY_NAME,
                metrics: []
                    .concat(conversionMetrics, conversionGoalMetrics)
                    .filter(function(metric) {
                        return metric.shown;
                    }),
            });
        }

        function findCategoryByName(categories, name) {
            return categories.filter(function(c) {
                return c.name === name;
            })[0];
        }

        function findMetricByValue(categories, metricValue) {
            // Find metric by value in given categories and subcategories
            var metric;
            for (var i = 0; i < categories.length; ++i) {
                var category = categories[i];
                metric = findMetricInCategoryByValue(category, metricValue);
                if (!metric && category.subcategories) {
                    metric = findMetricByValue(
                        category.subcategories,
                        metricValue
                    );
                }
                if (metric) return metric;
            }
            return null;
        }

        function findMetricInCategoryByValue(category, metricValue) {
            for (var j = 0; j < category.metrics.length; ++j) {
                var metric = category.metrics[j];
                if (metric.value === metricValue) {
                    return metric;
                }
            }
            return null;
        }

        function findMetricInCategoryByFieldGroup(
            category,
            fieldGroup,
            costMode
        ) {
            for (var metric, j = 0; j < category.metrics.length; ++j) {
                metric = category.metrics[j];
                if (
                    metric.fieldGroup &&
                    metric.costMode === costMode &&
                    metric.fieldGroup === fieldGroup
                ) {
                    return metric;
                }
            }
            return null;
        }

        function findMetricByCostMode(categories, metricValue, costMode) {
            var metric = findMetricByValue(categories, metricValue);

            if (!metric || !metric.fieldGroup) return null;

            for (var m, category, i = 0; i < categories.length; i++) {
                category = categories[i];

                m = findMetricInCategoryByFieldGroup(
                    category,
                    metric.fieldGroup,
                    costMode
                );
                if (m) return m;

                if (category.subcategories) {
                    for (var j = 0; j < category.subcategories.length; ++j) {
                        var subcategory = category.subcategories[j];
                        m = findMetricInCategoryByFieldGroup(
                            subcategory,
                            metric.fieldGroup,
                            costMode
                        );
                        if (m) return m;
                    }
                }
            }

            return null;
        }

        function createPlaceholderMetric(value) {
            var metric = {
                name: '<Dynamic metric>',
                value: value,
                placeholder: true,
            };

            if (value.indexOf('pixel_') >= 0) {
                metric.name = '<Pixel metric>';
            }

            if (value.indexOf('goal_') >= 0) {
                metric.name = '<Goal metric>';
            }

            if (value.indexOf('avg_cost_per_') === 0) {
                metric.name = 'CPA (' + metric.name + ')';
                metric.type = TYPE_CURRENCY;
                metric.fractionSize = 2;
            }

            return metric;
        }

        function createEmptyMetric() {
            return {
                value: null,
                name: 'None',
            };
        }

        return {
            METRICS: METRICS,
            getChartMetrics: getChartMetrics,
            insertDynamicMetrics: insertDynamicMetrics,
            findMetricByValue: findMetricByValue,
            findCategoryByName: findCategoryByName,
            findMetricByCostMode: findMetricByCostMode,
            createPlaceholderMetric: createPlaceholderMetric,
            createEmptyMetric: createEmptyMetric,
        };
    });
