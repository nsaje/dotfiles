var EntityPermissionValue = require('../../../../core/users/users.constants')
    .EntityPermissionValue;
var CategoryName = require('../../../../app.constants').CategoryName;
var ConversionPixelAttribution = require('../../../../core/conversion-pixels/conversion-pixel.constants')
    .ConversionPixelAttribution;
var ConversionPixelKPI = require('../../../../core/conversion-pixels/conversion-pixel.constants')
    .ConversionPixelKPI;

angular
    .module('one.widgets')
    .factory('zemChartMetricsService', function(
        zemAuthStore,
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
        var TYPE_PERCENT = 'percent';

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
                type: TYPE_PERCENT,
                fractionSize: 2,
                shown: true,
            },

            ETFM_CPC: {
                name: 'Avg. CPC',
                value: 'etfm_cpc',
                type: TYPE_CURRENCY,
                fractionSize: 3,
                shown: true,
                costMode: constants.costMode.PUBLIC,
            },
            ETFM_CPM: {
                name: 'Avg. CPM',
                value: 'etfm_cpm',
                type: TYPE_CURRENCY,
                fractionSize: 3,
                shown: true,
                costMode: constants.costMode.PUBLIC,
            },

            DATA_COST: {
                name: 'Actual Base Data Cost',
                value: 'data_cost',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                shown: 'zemauth.can_view_actual_costs',
            },
            MEDIA_COST: {
                name: 'Actual Base Media Spend',
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
                shownForEntity:
                    EntityPermissionValue.MEDIA_COST_DATA_COST_LICENCE_FEE,
            },
            E_MEDIA_COST: {
                name: 'Media Spend',
                value: 'e_media_cost',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                shown: 'zemauth.can_view_platform_cost_breakdown',
                shownForEntity:
                    EntityPermissionValue.MEDIA_COST_DATA_COST_LICENCE_FEE,
            },
            B_DATA_COST: {
                name: 'Base Data Cost',
                value: 'b_data_cost',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                shown: 'zemauth.can_see_service_fee',
                shownForEntity: EntityPermissionValue.BASE_COSTS_SERVICE_FEE,
            },
            B_MEDIA_COST: {
                name: 'Base Media Spend',
                value: 'b_media_cost',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                shown: 'zemauth.can_see_service_fee',
                shownForEntity: EntityPermissionValue.BASE_COSTS_SERVICE_FEE,
            },
            ETFM_COST: {
                name: 'Total Spend',
                value: 'etfm_cost',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                shown: true,
                costMode: constants.costMode.ANY,
            },
            ETF_COST: {
                name: 'Agency Spend',
                value: 'etf_cost',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                shown: 'zemauth.can_view_agency_cost_breakdown',
                shownForEntity: EntityPermissionValue.AGENCY_SPEND_MARGIN,
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
            BT_COST: {
                name: 'Base Platform Spend',
                value: 'bt_cost',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                shown: 'zemauth.can_see_service_fee',
                shownForEntity: EntityPermissionValue.BASE_COSTS_SERVICE_FEE,
                costMode: constants.costMode.ANY,
            },

            SERVICE_FEE: {
                name: 'Service Fee',
                value: 'service_fee',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                shown: 'zemauth.can_see_service_fee',
                shownForEntity: EntityPermissionValue.BASE_COSTS_SERVICE_FEE,
            },
            LICENSE_FEE: {
                name: 'License Fee',
                value: 'license_fee',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                shown: 'zemauth.can_view_platform_cost_breakdown',
                shownForEntity:
                    EntityPermissionValue.MEDIA_COST_DATA_COST_LICENCE_FEE,
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
                type: TYPE_PERCENT,
                fractionSize: 2,
                shown: true,
            },
            PERCENT_NEW_USERS: {
                name: '% New Users',
                value: 'percent_new_users',
                type: TYPE_PERCENT,
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
                type: TYPE_PERCENT,
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
            ETFM_COST_PER_MINUTE: {
                name: 'Avg. Cost per Minute',
                value: 'avg_etfm_cost_per_minute',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                costMode: constants.costMode.PUBLIC,
                shown: true,
            },
            ETFM_COST_PER_PAGEVIEW: {
                name: 'Avg. Cost per Pageview',
                value: 'avg_etfm_cost_per_pageview',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                costMode: constants.costMode.PUBLIC,
                shown: true,
            },
            ETFM_COST_PER_VISIT: {
                name: 'Avg. Cost per Visit',
                value: 'avg_etfm_cost_per_visit',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                costMode: constants.costMode.PUBLIC,
                shown: true,
            },
            ETFM_COST_PER_NON_BOUNCED_VISIT: {
                name: 'Avg. Cost per Non-Bounced Visit',
                value: 'avg_etfm_cost_per_non_bounced_visit',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                costMode: constants.costMode.PUBLIC,
                shown: true,
            },
            ETFM_COST_PER_NEW_VISITOR: {
                name: 'Avg. Cost per New Visitor',
                value: 'avg_etfm_cost_per_new_visitor',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                costMode: constants.costMode.PUBLIC,
                shown: true,
            },
            ETFM_COST_PER_UNIQUE_USER: {
                name: 'Avg. Cost per Unique User',
                value: 'avg_etfm_cost_per_unique_user',
                type: TYPE_CURRENCY,
                fractionSize: 2,
                costMode: constants.costMode.PUBLIC,
                shown: true,
            },

            VIDEO_START: {
                name: 'Video Start',
                value: 'video_start',
                type: TYPE_NUMBER,
                shown: true,
            },
            VIDEO_PROGRESS_3S: {
                name: 'Video Progress 3s',
                value: 'video_progress_3s',
                type: TYPE_NUMBER,
                shown: true,
            },
            VIDEO_FIRST_QUARTILE: {
                name: 'Video First Quartile',
                value: 'video_first_quartile',
                type: TYPE_NUMBER,
                shown: true,
            },
            VIDEO_MIDPOINT: {
                name: 'Video Midpoint',
                value: 'video_midpoint',
                type: TYPE_NUMBER,
                shown: true,
            },
            VIDEO_THIRD_QUARTILE: {
                name: 'Video Third Quartile',
                value: 'video_third_quartile',
                type: TYPE_NUMBER,
                shown: true,
            },
            VIDEO_COMPLETE: {
                name: 'Video Complete',
                value: 'video_complete',
                type: TYPE_NUMBER,
                shown: true,
            },

            VIDEO_START_PERCENT: {
                name: '% Video Start',
                value: 'video_start_percent',
                type: TYPE_PERCENT,
                shown: true,
            },
            VIDEO_PROGRESS_3S_PERCENT: {
                name: '% Video Progress 3s',
                value: 'video_progress_3s_percent',
                type: TYPE_PERCENT,
                shown: true,
            },
            VIDEO_FIRST_QUARTILE_PERCENT: {
                name: '% Video First Quartile',
                value: 'video_first_quartile_percent',
                type: TYPE_PERCENT,
                shown: true,
            },
            VIDEO_MIDPOINT_PERCENT: {
                name: '% Video Midpoint',
                value: 'video_midpoint_percent',
                type: TYPE_PERCENT,
                shown: true,
            },
            VIDEO_THIRD_QUARTILE_PERCENT: {
                name: '% Video Third Quartile',
                value: 'video_third_quartile_percent',
                type: TYPE_PERCENT,
                shown: true,
            },
            VIDEO_COMPLETE_PERCENT: {
                name: '% Video Complete',
                value: 'video_complete_percent',
                type: TYPE_PERCENT,
                shown: true,
            },

            VIDEO_ETFM_CPV: {
                name: 'Avg. CPV',
                value: 'video_etfm_cpv',
                type: TYPE_CURRENCY,
                fractionSize: 3,
                shown: true,
                costMode: constants.costMode.PUBLIC,
            },
            VIDEO_ETFM_CPCV: {
                name: 'Avg. CPCV',
                value: 'video_etfm_cpcv',
                type: TYPE_CURRENCY,
                fractionSize: 3,
                shown: true,
                costMode: constants.costMode.PUBLIC,
            },
            MRC50_MEASURABLE: {
                name: 'Measurable Impressions',
                value: 'mrc50_measurable',
                type: TYPE_NUMBER,
                shown: true,
                shortName: 'Measurable',
            },
            MRC50_VIEWABLE: {
                name: 'Viewable Impressions',
                value: 'mrc50_viewable',
                type: TYPE_NUMBER,
                shown: true,
                shortName: 'Viewable',
            },
            MRC50_NON_MEASURABLE: {
                name: 'Not-Measurable Impr.',
                value: 'mrc50_non_measurable',
                type: TYPE_NUMBER,
                shown: true,
                shortName: 'Not-Measurable',
            },
            MRC50_NON_VIEWABLE: {
                name: 'Not-Viewable Impressions',
                value: 'mrc50_non_viewable',
                type: TYPE_NUMBER,
                shown: true,
                shortName: 'Not-Viewable',
            },
            MRC50_MEASURABLE_PERCENT: {
                name: '% Measurable Impressions',
                value: 'mrc50_measurable_percent',
                type: TYPE_PERCENT,
                fractionSize: 2,
                shown: true,
                shortName: '% Measurable',
            },
            MRC50_VIEWABLE_PERCENT: {
                name: '% Viewable Impressions',
                value: 'mrc50_viewable_percent',
                type: TYPE_PERCENT,
                fractionSize: 2,
                shown: true,
                shortName: '% Viewable',
            },
            MRC50_VIEWABLE_DISTRIBUTION: {
                name: 'Impression Distribution (Viewable)',
                value: 'mrc50_viewable_distribution',
                type: TYPE_PERCENT,
                fractionSize: 2,
                shown: true,
                shortName: 'Viewable Dist.',
            },
            MRC50_NON_MEASURABLE_DISTRIBUTION: {
                name: 'Impression Distribution (Not-Measurable)',
                value: 'mrc50_non_measurable_distribution',
                type: TYPE_PERCENT,
                fractionSize: 2,
                shown: true,
                shortName: 'Not-Measurable Dist.',
            },
            MRC50_NON_VIEWABLE_DISTRIBUTION: {
                name: 'Impression Distribution (Not-Viewable)',
                value: 'mrc50_non_viewable_distribution',
                type: TYPE_PERCENT,
                fractionSize: 2,
                shown: true,
                shortName: 'Not-Viewable Dist.',
            },
            ETFM_MRC50_VCPM: {
                name: 'Avg. VCPM',
                value: 'etfm_mrc50_vcpm',
                type: TYPE_CURRENCY,
                fractionSize: 3,
                shown: true,
                costMode: constants.costMode.PUBLIC,
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
                type: TYPE_PERCENT,
                fractionSize: 2,
                shown: ['zemauth.can_see_mrc100_metrics'],
                internal: 'zemauth.can_see_mrc100_metrics',
                shortName: '% Measurable',
            },
            MRC100_VIEWABLE_PERCENT: {
                name: '% MRC100 Viewable Impressions',
                value: 'mrc100_viewable_percent',
                type: TYPE_PERCENT,
                fractionSize: 2,
                shown: ['zemauth.can_see_mrc100_metrics'],
                internal: 'zemauth.can_see_mrc100_metrics',
                shortName: '% Viewable',
            },
            MRC100_VIEWABLE_DISTRIBUTION: {
                name: 'MRC100 Impression Distribution (Viewable)',
                value: 'mrc100_viewable_distribution',
                type: TYPE_PERCENT,
                fractionSize: 2,
                shown: ['zemauth.can_see_mrc100_metrics'],
                internal: 'zemauth.can_see_mrc100_metrics',
                shortName: 'Viewable Dist.',
            },
            MRC100_NON_MEASURABLE_DISTRIBUTION: {
                name: 'MRC100 Impression Distribution (Not-Measurable)',
                value: 'mrc100_non_measurable_distribution',
                type: TYPE_PERCENT,
                fractionSize: 2,
                shown: ['zemauth.can_see_mrc100_metrics'],
                internal: 'zemauth.can_see_mrc100_metrics',
                shortName: 'Not-Measurable Dist.',
            },
            MRC100_NON_VIEWABLE_DISTRIBUTION: {
                name: 'MRC100 Impression Distribution (Not-Viewable)',
                value: 'mrc100_non_viewable_distribution',
                type: TYPE_PERCENT,
                fractionSize: 2,
                shown: ['zemauth.can_see_mrc100_metrics'],
                internal: 'zemauth.can_see_mrc100_metrics',
                shortName: 'Not-Viewable Dist.',
            },
            ETFM_MRC100_VCPM: {
                name: 'Avg. MRC100 VCPM',
                value: 'etfm_mrc100_vcpm',
                type: TYPE_CURRENCY,
                fractionSize: 3,
                shown: ['zemauth.can_see_mrc100_metrics'],
                costMode: constants.costMode.PUBLIC,
                internal: 'zemauth.can_see_mrc100_metrics',
                shortName: 'Avg. VCPM',
            },
            VAST4_MEASURABLE: {
                name: 'Video Measurable Impressions',
                value: 'vast4_measurable',
                type: TYPE_NUMBER,
                shown: ['zemauth.can_see_vast4_metrics'],
                internal: 'zemauth.can_see_vast4_metrics',
                shortName: 'Measurable',
            },
            VAST4_VIEWABLE: {
                name: 'Video Viewable Impressions',
                value: 'vast4_viewable',
                type: TYPE_NUMBER,
                shown: ['zemauth.can_see_vast4_metrics'],
                internal: 'zemauth.can_see_vast4_metrics',
                shortName: 'Viewable',
            },
            VAST4_NON_MEASURABLE: {
                name: 'Video Non-Measurable',
                value: 'vast4_non_measurable',
                type: TYPE_NUMBER,
                shown: ['zemauth.can_see_vast4_metrics'],
                internal: 'zemauth.can_see_vast4_metrics',
                shortName: 'Not-Measurable',
            },
            VAST4_NON_VIEWABLE: {
                name: 'Video Non-Viewable',
                value: 'vast4_non_viewable',
                type: TYPE_NUMBER,
                shown: ['zemauth.can_see_vast4_metrics'],
                internal: 'zemauth.can_see_vast4_metrics',
                shortName: 'Not-Viewable',
            },
            VAST4_MEASURABLE_PERCENT: {
                name: '% Video Measurable Impressions',
                value: 'vast4_measurable_percent',
                type: TYPE_PERCENT,
                fractionSize: 2,
                shown: ['zemauth.can_see_vast4_metrics'],
                internal: 'zemauth.can_see_vast4_metrics',
                shortName: '% Measurable',
            },
            VAST4_VIEWABLE_PERCENT: {
                name: '% Video Viewable Impressions',
                value: 'vast4_viewable_percent',
                type: TYPE_PERCENT,
                fractionSize: 2,
                shown: ['zemauth.can_see_vast4_metrics'],
                internal: 'zemauth.can_see_vast4_metrics',
                shortName: '% Viewable',
            },
            VAST4_VIEWABLE_DISTRIBUTION: {
                name: 'Video Impression Distribution (Viewable)',
                value: 'vast4_viewable_distribution',
                type: TYPE_PERCENT,
                fractionSize: 2,
                shown: ['zemauth.can_see_vast4_metrics'],
                internal: 'zemauth.can_see_vast4_metrics',
                shortName: 'Viewable Dist.',
            },
            VAST4_NON_MEASURABLE_DISTRIBUTION: {
                name: 'Video Impression Distribution (Not-Measurable)',
                value: 'vast4_non_measurable_distribution',
                type: TYPE_PERCENT,
                fractionSize: 2,
                shown: ['zemauth.can_see_vast4_metrics'],
                internal: 'zemauth.can_see_vast4_metrics',
                shortName: 'Not-Measurable Dist.',
            },
            VAST4_NON_VIEWABLE_DISTRIBUTION: {
                name: 'Video Impression Distribution (Not-Viewable)',
                value: 'vast4_non_viewable_distribution',
                type: TYPE_PERCENT,
                fractionSize: 2,
                shown: ['zemauth.can_see_vast4_metrics'],
                internal: 'zemauth.can_see_vast4_metrics',
                shortName: 'Not-Viewable Dist.',
            },
            ETFM_VAST4_VCPM: {
                name: 'Avg. VAST4 VCPM',
                value: 'etfm_vast4_vcpm',
                type: TYPE_CURRENCY,
                fractionSize: 3,
                shown: ['zemauth.can_see_vast4_metrics'],
                costMode: constants.costMode.PUBLIC,
                internal: 'zemauth.can_see_vast4_metrics',
                shortName: 'Avg. VCPM',
            },
        };
        /* eslint-enable max-len */

        var TRAFFIC_ACQUISITION = [
            METRICS.IMPRESSIONS,
            METRICS.CLICKS,
            METRICS.CTR,
            METRICS.ETFM_CPC,
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
            METRICS.ETFM_VAST4_VCPM,
        ];

        var COST_METRICS = [
            METRICS.MEDIA_COST,
            METRICS.E_MEDIA_COST,
            METRICS.B_MEDIA_COST,
            METRICS.DATA_COST,
            METRICS.E_DATA_COST,
            METRICS.B_DATA_COST,
            METRICS.SERVICE_FEE,
            METRICS.LICENSE_FEE,
            METRICS.ETFM_COST,
            METRICS.ETF_COST,
            METRICS.ET_COST,
            METRICS.BT_COST,
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
            METRICS.ETFM_COST_PER_VISIT,
            METRICS.ETFM_COST_PER_NEW_VISITOR,
            METRICS.ETFM_COST_PER_PAGEVIEW,
            METRICS.ETFM_COST_PER_NON_BOUNCED_VISIT,
            METRICS.ETFM_COST_PER_MINUTE,
            METRICS.ETFM_COST_PER_UNIQUE_USER,
        ];

        var VIDEO_METRICS = [
            METRICS.VIDEO_START,
            METRICS.VIDEO_PROGRESS_3S,
            METRICS.VIDEO_FIRST_QUARTILE,
            METRICS.VIDEO_MIDPOINT,
            METRICS.VIDEO_THIRD_QUARTILE,
            METRICS.VIDEO_COMPLETE,
            METRICS.VIDEO_ETFM_CPV,
            METRICS.VIDEO_ETFM_CPCV,
        ];

        var AUDIENCE_METRICS = [].concat(POST_CLICK_METRICS, GOAL_METRICS);

        ////////////////////////////////////////////////////////////////////////////////////
        // Service functions
        //
        function getChartMetrics() {
            var categories = [];
            categories.push({
                name: CategoryName.COST,
                metrics: createMetrics(COST_METRICS),
            });
            categories.push({
                name: CategoryName.TRAFFIC,
                metrics: createMetrics(TRAFFIC_ACQUISITION),
            });
            categories.push({
                name: CategoryName.MRC50,
                metrics: createMetrics(MRC50_VIEWABILITY_METRICS),
                isNewFeature: true,
            });
            categories.push({
                name: CategoryName.MRC100,
                metrics: createMetrics(MRC100_VIEWABILITY_METRICS),
                isNewFeature: true,
            });
            categories.push({
                name: CategoryName.AUDIENCE,
                metrics: createMetrics(AUDIENCE_METRICS),
            });
            categories.push({
                name: CategoryName.VIDEO,
                metrics: createMetrics(VIDEO_METRICS),
            });
            categories.push({
                name: CategoryName.VAST4,
                metrics: createMetrics(VAST4_VIEWABILITY_METRICS),
                isNewFeature: true,
            });

            return categories;
        }

        function checkPermissions(metrics) {
            var activeAccount = zemNavigationNewService.getActiveAccount();
            // Go through all the metrics and convert permissions to boolean when needed
            metrics.forEach(function(metric) {
                metric.internal = zemUtils.convertPermission(
                    metric.internal,
                    zemAuthStore.isPermissionInternal.bind(zemAuthStore)
                );

                if (metric.shownForEntity) {
                    if (activeAccount) {
                        metric.shown = zemAuthStore.hasPermissionOn(
                            activeAccount.data.agencyId,
                            activeAccount.id,
                            metric.shownForEntity
                        );
                    } else {
                        metric.shown = zemAuthStore.hasPermissionOnAnyEntity(
                            metric.shownForEntity
                        );
                    }
                } else {
                    metric.shown = zemUtils.convertPermission(
                        metric.shown,
                        zemAuthStore.hasPermission.bind(zemAuthStore)
                    );
                }
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
            if (!findCategoryByName(categories, CategoryName.PIXELS)) {
                insertPixelCategory(categories, pixels);
            }

            if (!findCategoryByName(categories, CategoryName.CONVERSIONS)) {
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

                generatePixelMetrics(
                    pixelSubCategory,
                    pixel,
                    options.conversionWindows,
                    '',
                    ' - Click attr.',
                    ConversionPixelAttribution.CLICK
                );
                generatePixelMetrics(
                    pixelSubCategory,
                    pixel,
                    options.conversionWindowsViewthrough,
                    '_view',
                    ' - View attr.',
                    ConversionPixelAttribution.VIEW
                );

                pixelSubcategories.push(pixelSubCategory);
            });

            categories.push({
                name: CategoryName.PIXELS,
                description: 'Choose conversion window in days.',
                metrics: [],
                subcategories: pixelSubcategories,
            });
        }

        function generatePixelMetrics(
            pixelSubCategory,
            pixel,
            conversionWindows,
            fieldSuffix,
            columnSuffix,
            attribution
        ) {
            var pixelMetrics = [];

            angular.forEach(conversionWindows, function(conversionWindow) {
                var metricValue =
                    pixel.prefix + '_' + conversionWindow.value + fieldSuffix;

                pixelMetrics.push({
                    value: metricValue,
                    name:
                        pixel.name + ' ' + conversionWindow.name + columnSuffix,
                    shown: true,
                    window: conversionWindow.value,
                    attribution: attribution,
                    performance: ConversionPixelKPI.CONVERSIONS,
                    pixel: pixel.name,
                });

                pixelMetrics.push({
                    value: 'avg_etfm_cost_per_' + metricValue,
                    name:
                        'CPA (' +
                        pixel.name +
                        ' ' +
                        conversionWindow.name +
                        columnSuffix +
                        ')',
                    type: TYPE_CURRENCY,
                    fractionSize: 2,
                    costMode: constants.costMode.PUBLIC,
                    shown: true,
                    window: conversionWindow.value,
                    attribution: attribution,
                    performance: ConversionPixelKPI.CPA,
                    pixel: pixel.name,
                });

                pixelMetrics.push({
                    value: 'conversion_rate_per_' + metricValue,
                    name:
                        'Conversion rate (' +
                        pixel.name +
                        ' ' +
                        conversionWindow.name +
                        columnSuffix +
                        ')',
                    type: TYPE_PERCENT,
                    fractionSize: 2,
                    costMode: constants.costMode.PUBLIC,
                    shown: true,
                    window: conversionWindow.value,
                    attribution: attribution,
                    performance: ConversionPixelKPI.CONVERSION_RATE,
                    pixel: pixel.name,
                });
            });

            checkPermissions(pixelMetrics);

            pixelSubCategory.metrics = pixelSubCategory.metrics.concat(
                pixelMetrics
            );
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
                    value: 'avg_etfm_cost_per_' + goal.id,
                    name: 'CPA (' + goal.name + ')',
                    type: TYPE_CURRENCY,
                    fractionSize: 2,
                    costMode: constants.costMode.PUBLIC,
                    shown: true,
                });
            });

            checkPermissions(conversionMetrics);
            checkPermissions(conversionGoalMetrics);

            categories.push({
                name: CategoryName.CONVERSIONS,
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

            if (value.indexOf('avg_etfm_cost_per_') === 0) {
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
