var EntityPermissionValue = require('../../../../../core/users/users.constants')
    .EntityPermissionValue;
var CategoryName = require('../../../../../app.constants').CategoryName;
var arrayHelpers = require('../../../../../shared/helpers/array.helpers');

angular
    .module('one.widgets')
    .factory('zemGridEndpointColumns', function(
        zemAuthStore,
        zemGridConstants,
        zemUtils,
        zemNavigationNewService
    ) {
        // eslint-disable-line max-len
        var CONVERSION_RATE_PREFIX = 'conversion_rate_per_';
        var AVG_ETFM_COST_PREFIX = 'avg_etfm_cost_per_';
        var ETFM_ROAS_PREFIX = 'etfm_roas_';

        var CONVERSION_GOALS_PLACEHOLDER = 'conversion_goals_placeholder';
        var PIXELS_PLACEHOLDER = 'pixels_placeholder';

        // //////////////////////////////////////////////////////////////////////////////////////////////////
        // COLUMN DEFINITIONS
        //
        var COLUMNS = {
            agencyId: {
                shown: true,
                order: false,
                initialOrder: zemGridConstants.gridColumnOrder.ASC,
                name: 'Agency ID',
                field: 'agency_id',
                type: zemGridConstants.gridColumnTypes.TEXT,
                help: 'The ID number of your agency.',
            },
            accountId: {
                shown: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.ASC,
                name: 'Account ID',
                field: 'account_id',
                type: zemGridConstants.gridColumnTypes.TEXT,
                help: 'The ID number of your account.',
            },
            campaignId: {
                shown: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.ASC,
                name: 'Campaign ID',
                field: 'campaign_id',
                type: zemGridConstants.gridColumnTypes.TEXT,
                help: 'The ID number of your campaign.',
            },
            adGroupId: {
                shown: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.ASC,
                name: 'Ad Group ID',
                field: 'ad_group_id',
                type: zemGridConstants.gridColumnTypes.TEXT,
                help: 'The ID number of your ad group.',
            },
            contentAdId: {
                shown: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.ASC,
                name: 'Content Ad ID',
                field: 'content_ad_id',
                type: zemGridConstants.gridColumnTypes.TEXT,
                help: 'The ID number of your content ad.',
            },
            amplifyAdId: {
                name: 'Outbrain Ad ID',
                field: 'amplify_promoted_link_id',
                type: zemGridConstants.gridColumnTypes.TEXT,
                totalRow: false,
                help: 'The ID of your content ad in Outbrain Amplify.',
                order: false,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                internal: 'zemauth.can_see_amplify_ad_id_column',
                shown: 'zemauth.can_see_amplify_ad_id_column',
            },
            sourceId: {
                shown: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.ASC,
                name: 'Source ID',
                field: 'source_id',
                type: zemGridConstants.gridColumnTypes.TEXT,
                help: 'The ID number of your media source.',
            },
            sourceSlug: {
                shown: true,
                name: 'Source Slug',
                field: 'source_slug',
                type: zemGridConstants.gridColumnTypes.TEXT,
                help: 'The slug identifier of your media source.',
            },
            name: {
                name: '', // Branded based on breakdown
                help: '', // Branded based on breakdown
                field: 'breakdown_name',
                type: zemGridConstants.gridColumnTypes.BREAKDOWN,
                shown: true,
                totalRow: false,
                order: true,
                orderField: 'name',
                initialOrder: zemGridConstants.gridColumnOrder.ASC,
            },
            actions: {
                name: 'Actions',
                type: zemGridConstants.gridColumnTypes.ACTIONS,
                shown: true,
            },
            state: {
                name: '', // Branded based on breakdown
                help: '', // Branded based on breakdown
                field: 'state',
                type: zemGridConstants.gridColumnTypes.STATE_SELECTOR,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.ASC,
                internal: false,
                shown: false,
                totalRow: false,
                archivedField: 'archived',
            },
            status: {
                name: '', // Branded based on breakdown
                help: '', // Branded based on breakdown
                field: 'status',
                type: zemGridConstants.gridColumnTypes.STATUS,
                shown: true,
                totalRow: false,
                order: true,
                orderField: 'status',
                initialOrder: zemGridConstants.gridColumnOrder.ASC,
            },
            submissionStatus: {
                name: 'Submission Status',
                help: 'Current submission status.',
                field: 'submission_status',
                type: zemGridConstants.gridColumnTypes.SUBMISSION_STATUS,
                shown: true,
                totalRow: false,
                order: false,
                initialOrder: zemGridConstants.gridColumnOrder.ASC,
            },
            performance: {
                nameCssClass: 'performance-icon',
                field: 'performance',
                type: zemGridConstants.gridColumnTypes.PERFORMANCE_INDICATOR,
                totalRow: false,
                help: 'Goal performance indicator',
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.ASC,
                internal: false,
                shown: true,
            },
            agency: {
                name: 'Agency',
                field: 'agency',
                type: zemGridConstants.gridColumnTypes.TEXT,
                totalRow: false,
                help: 'Agency to which this account belongs.',
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                internal: false,
                shown: true,
            },
            defaultAccountManager: {
                name: 'Account Manager',
                field: 'default_account_manager',
                type: zemGridConstants.gridColumnTypes.TEXT,
                totalRow: false,
                help:
                    'Account manager responsible for the campaign and the communication with the client.',
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                internal: 'zemauth.can_see_managers_in_accounts_table',
                shown: 'zemauth.can_see_managers_in_accounts_table',
            },
            defaultSalesRepresentative: {
                name: 'Sales Representative',
                field: 'default_sales_representative',
                type: zemGridConstants.gridColumnTypes.TEXT,
                totalRow: false,
                help:
                    'Sales representative responsible for the campaign and the communication with the client.',
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                internal: 'zemauth.can_see_managers_in_accounts_table',
                shown: 'zemauth.can_see_managers_in_accounts_table',
            },
            defaultCsRepresentative: {
                name: 'CS Representative',
                field: 'default_cs_representative',
                type: zemGridConstants.gridColumnTypes.TEXT,
                totalRow: false,
                help:
                    'Customer success manager responsible for the campaign and the communication with the client.',
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                internal: 'zemauth.can_see_managers_in_accounts_table',
                shown: 'zemauth.can_see_managers_in_accounts_table',
            },
            obSalesRepresentative: {
                name: 'OB sales Representative',
                field: 'ob_sales_representative',
                type: zemGridConstants.gridColumnTypes.TEXT,
                totalRow: false,
                help:
                    'Outbrain representative responsible for the account and the communication with the client.',
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                internal: 'zemauth.can_see_managers_in_accounts_table',
                shown: 'zemauth.can_see_managers_in_accounts_table',
            },
            obAccountManager: {
                name: 'OB account manager',
                field: 'ob_account_manager',
                type: zemGridConstants.gridColumnTypes.TEXT,
                totalRow: false,
                help:
                    'Outbrain Manager responsible for the account and the communication with the client.',
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                internal: 'zemauth.can_see_managers_in_accounts_table',
                shown: 'zemauth.can_see_managers_in_accounts_table',
            },
            campaignManager: {
                name: 'Campaign Manager',
                field: 'campaign_manager',
                type: zemGridConstants.gridColumnTypes.TEXT,
                totalRow: false,
                help:
                    'Campaign manager responsible for the campaign and the communication with the client.',
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                internal: 'zemauth.can_see_managers_in_campaigns_table',
                shown: 'zemauth.can_see_managers_in_campaigns_table',
            },
            accountType: {
                name: 'Account Type',
                field: 'account_type',
                type: zemGridConstants.gridColumnTypes.TEXT,
                totalRow: false,
                help: 'Type of account.',
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                internal: 'zemauth.can_see_account_type',
                shown: 'zemauth.can_see_account_type',
            },
            salesforceUrl: {
                name: 'SalesForce Link',
                field: 'salesforce_url',
                type: zemGridConstants.gridColumnTypes.ICON_LINK,
                totalRow: false,
                help: 'URL of this account in SalesForce',
                order: false,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                internal: 'zemauth.can_see_salesforce_url',
                shown: 'zemauth.can_see_salesforce_url',
            },
            sspdUrl: {
                name: 'SSPD Link',
                field: 'sspd_url',
                type: zemGridConstants.gridColumnTypes.ICON_LINK,
                totalRow: false,
                help: 'URL to SSP dashboard',
                order: false,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                internal: 'zemauth.can_see_sspd_url',
                shown: 'zemauth.can_see_sspd_url',
            },
            campaignType: {
                name: 'Campaign Type',
                field: 'campaign_type',
                type: zemGridConstants.gridColumnTypes.TEXT,
                totalRow: false,
                order: false,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                internal: false,
                shown: true,
            },

            // Media source
            supplyDashUrl: {
                name: 'Link',
                field: 'supply_dash_url',
                type: zemGridConstants.gridColumnTypes.ICON_LINK,
                totalRow: false,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                internal: 'zemauth.supply_dash_link_view',
                shown: 'zemauth.supply_dash_link_view',
            },

            // AdGroup Media Sources
            dailyBudgetSetting: {
                name: 'Daily Spend Cap',
                field: 'daily_budget',
                fractionSize: 0,
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                shown: true,
                help: 'Maximum media spend cap per day.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                defaultValue: '',
            },

            // Content Ad
            imageUrls: {
                name: 'Thumbnail',
                field: 'image_urls',
                type: zemGridConstants.gridColumnTypes.THUMBNAIL,
                shown: true,
                totalRow: false,
                titleField: 'title',
                order: true,
                orderField: 'image_hash',
                initialOrder: zemGridConstants.gridColumnOrder.ASC,
            },
            urlLink: {
                name: 'URL',
                field: 'urlLink',
                type: zemGridConstants.gridColumnTypes.TEXT_LINK,
                shown: true,
                help: 'The web address of the content ad.',
                totalRow: false,
                titleField: 'url',
                order: true,
                orderField: 'url',
                initialOrder: zemGridConstants.gridColumnOrder.ASC,
            },
            uploadTime: {
                name: 'Uploaded',
                field: 'upload_time',
                type: zemGridConstants.gridColumnTypes.DATE_TIME,
                shown: true,
                help: 'The time when the content ad was uploaded.',
                totalRow: false,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            batchId: {
                shown: false, // not shown (used internally)
                name: 'Batch Id',
                field: 'batch_id',
                type: zemGridConstants.gridColumnTypes.TEXT,
            },
            batchName: {
                name: 'Batch Name',
                field: 'batch_name',
                type: zemGridConstants.gridColumnTypes.TEXT,
                shown: true,
                help: 'The name of the upload batch.',
                totalRow: false,
                titleField: 'batch_name',
                order: true,
                orderField: 'batch_name',
                initialOrder: zemGridConstants.gridColumnOrder.ASC,
            },
            displayUrl: {
                name: 'Display URL',
                field: 'display_url',
                type: zemGridConstants.gridColumnTypes.TEXT,
                shown: true,
                help: "Advertiser's display URL.",
                totalRow: false,
                titleField: 'display_url',
                order: true,
                orderField: 'display_url',
                initialOrder: zemGridConstants.gridColumnOrder.ASC,
            },
            brandName: {
                name: 'Brand Name',
                field: 'brand_name',
                type: zemGridConstants.gridColumnTypes.TEXT,
                shown: true,
                help: "Advertiser's brand name",
                totalRow: false,
                titleField: 'brand_name',
                order: true,
                orderField: 'brand_name',
                initialOrder: zemGridConstants.gridColumnOrder.ASC,
            },
            description: {
                name: 'Description',
                field: 'description',
                type: zemGridConstants.gridColumnTypes.TEXT,
                shown: true,
                help: 'Description of a content ad.',
                totalRow: false,
                titleField: 'description',
                order: true,
                orderField: 'description',
                initialOrder: zemGridConstants.gridColumnOrder.ASC,
            },
            callToAction: {
                name: 'Call to action',
                field: 'call_to_action',
                type: zemGridConstants.gridColumnTypes.TEXT,
                shown: true,
                help: 'Call to action text.',
                totalRow: false,
                titleField: 'call_to_action',
                order: true,
                orderField: 'call_to_action',
                initialOrder: zemGridConstants.gridColumnOrder.ASC,
            },
            label: {
                name: 'Label',
                field: 'label',
                type: zemGridConstants.gridColumnTypes.TEXT,
                shown: true,
                help: "Content ad's label.",
                totalRow: false,
                titleField: 'label',
                order: true,
                orderField: 'label',
                initialOrder: zemGridConstants.gridColumnOrder.ASC,
            },
            impressionTrackers: {
                name: 'Impression trackers',
                field: 'tracker_urls',
                type: zemGridConstants.gridColumnTypes.TEXT,
                shown: true,
                help: "Content ad's impression trackers.",
                totalRow: false,
                titleField: 'tracker_urls',
                order: true,
                orderField: 'tracker_urls',
                initialOrder: zemGridConstants.gridColumnOrder.ASC,
            },
            adType: {
                name: 'Creative Type',
                field: 'creative_type',
                type: zemGridConstants.gridColumnTypes.TEXT,
                totalRow: false,
                titleField: 'creative_type',
                order: true,
                orderField: 'creative_type',
                initialOrder: zemGridConstants.gridColumnOrder.ASC,
                shown: true,
            },
            creativeSize: {
                name: 'Creative Size',
                field: 'creative_size',
                type: zemGridConstants.gridColumnTypes.TEXT,
                totalRow: false,
                titleField: 'creative_size',
                order: true,
                orderField: 'creative_size',
                initialOrder: zemGridConstants.gridColumnOrder.ASC,
                shown: true,
            },

            // Publisher
            domain: {
                name: 'Publisher',
                field: 'domain',
                type: zemGridConstants.gridColumnTypes.TEXT,
                shown: false,
                totalRow: false,
                help: 'A publisher where your content is being promoted.',
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.ASC,
            },
            domainLink: {
                name: 'Link',
                field: 'domain_link',
                type: zemGridConstants.gridColumnTypes.VISIBLE_LINK,
                shown: true,
                totalRow: false,
                help:
                    'Link to a publisher where your content is being promoted.',
                order: false,
                initialOrder: zemGridConstants.gridColumnOrder.ASC,
            },
            exchange: {
                name: 'Media Source',
                field: 'exchange',
                type: zemGridConstants.gridColumnTypes.TEXT,
                shown: true,
                totalRow: false,
                help: 'An exchange where your content is being promoted.',
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.ASC,
            },
            bidModifier: {
                name: 'Bid Modifier',
                field: 'bid_modifier',
                type: zemGridConstants.gridColumnTypes.BID_MODIFIER_FIELD,
                totalRow: false,
                help:
                    'Bid modifiers allow you to adjust bid per selected breakdown.',
                shown: [
                    {
                        permissions: [],
                        breakdowns: [
                            constants.breakdown.CONTENT_AD,
                            constants.breakdown.COUNTRY,
                            constants.breakdown.STATE,
                            constants.breakdown.DMA,
                            constants.breakdown.DEVICE,
                            constants.breakdown.ENVIRONMENT,
                            constants.breakdown.OPERATING_SYSTEM,
                            constants.breakdown.PUBLISHER,
                            constants.breakdown.MEDIA_SOURCE,
                            constants.breakdown.PLACEMENT,
                            constants.breakdown.BROWSER,
                            constants.breakdown.CONNECTION_TYPE,
                        ],
                    },
                ],
            },
            amplifyLivePreview: {
                name: 'Ad Preview',
                field: 'amplify_live_preview_link',
                type: zemGridConstants.gridColumnTypes.ICON_LINK,
                totalRow: false,
                help: 'See the live preview of your content ad.',
                order: false,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                shown: 'zemauth.can_see_amplify_live_preview',
            },

            // Costs
            mediaCost: {
                name: 'Actual Base Media Spend',
                field: 'media_cost',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                totalRow: true,
                help: 'Amount spent per media source, including overspend.',
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                internal: 'zemauth.can_view_actual_costs',
                shown: 'zemauth.can_view_actual_costs',
                supportsRefunds: true,
            },
            bMediaCost: {
                name: 'Base Media Spend',
                field: 'b_media_cost',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                totalRow: true,
                help: 'Media spend without service fee.',
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                shownForEntity: EntityPermissionValue.BASE_COSTS_SERVICE_FEE,
            },
            eMediaCost: {
                name: 'Media Spend',
                field: 'e_media_cost',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                totalRow: true,
                help: 'Amount spent per media source.',
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                shownForEntity:
                    EntityPermissionValue.MEDIA_COST_DATA_COST_LICENCE_FEE,
                supportsRefunds: true,
            },
            dataCost: {
                name: 'Actual Base Data Spend',
                field: 'data_cost',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                totalRow: true,
                help:
                    'Additional targeting/segmenting costs, including overspend.',
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                internal: 'zemauth.can_view_actual_costs',
                shown: 'zemauth.can_view_actual_costs',
            },
            bDataCost: {
                name: 'Base Data Spend',
                field: 'b_data_cost',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                totalRow: true,
                help: 'Data spend without service fee.',
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                shownForEntity: EntityPermissionValue.BASE_COSTS_SERVICE_FEE,
            },
            eDataCost: {
                name: 'Data Spend',
                field: 'e_data_cost',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                totalRow: true,
                help:
                    "Additional targeting/segmenting costs. If you are running a video campaign with video files hosted by Zemanta we'll also display the additional video serving cost in this column.",
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                shownForEntity:
                    EntityPermissionValue.MEDIA_COST_DATA_COST_LICENCE_FEE,
            },
            serviceFee: {
                name: 'Service Fee',
                field: 'service_fee',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                totalRow: true,
                help: 'Agency’s service fee.',
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                shownForEntity: EntityPermissionValue.BASE_COSTS_SERVICE_FEE,
            },
            licenseFee: {
                name: 'License Fee',
                field: 'license_fee',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                totalRow: true,
                help: 'Zemanta One platform usage cost.',
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                shownForEntity:
                    EntityPermissionValue.MEDIA_COST_DATA_COST_LICENCE_FEE,
                supportsRefunds: true,
            },
            margin: {
                name: 'Margin',
                field: 'margin',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                totalRow: true,
                help: "Agency's margin",
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                shownForEntity: EntityPermissionValue.AGENCY_SPEND_MARGIN,
                supportsRefunds: true,
            },
            etfmCost: {
                name: 'Total Spend',
                field: 'etfm_cost',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                totalRow: true,
                help: 'Sum of media spend, data spend, license fee and margin.',
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                shown: true,
                costMode: constants.costMode.ANY,
                supportsRefunds: true,
            },
            etfCost: {
                name: 'Agency Spend',
                field: 'etf_cost',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                totalRow: true,
                help: 'Sum of media spend, data spend and license fee.',
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                shownForEntity: EntityPermissionValue.AGENCY_SPEND_MARGIN,
                costMode: constants.costMode.ANY,
                supportsRefunds: true,
            },
            etCost: {
                name: 'Platform Spend',
                field: 'et_cost',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                totalRow: true,
                help: 'Sum of media spend and data spend.',
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                internal: 'zemauth.can_view_platform_cost_breakdown_derived',
                shown: 'zemauth.can_view_platform_cost_breakdown_derived',
                costMode: constants.costMode.ANY,
                supportsRefunds: true,
            },
            btCost: {
                name: 'Base Platform Spend',
                field: 'bt_cost',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                totalRow: true,
                help: 'Platform spend without service fee.',
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                shownForEntity: EntityPermissionValue.BASE_COSTS_SERVICE_FEE,
                costMode: constants.costMode.ANY,
            },
            atCost: {
                name: 'Actual Base Platform Spend',
                field: 'at_cost',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                totalRow: true,
                help: 'Sum of actual media spend and data spend.',
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                internal: 'zemauth.can_view_actual_costs',
                shown: [
                    'zemauth.can_view_actual_costs',
                    'zemauth.can_view_platform_cost_breakdown_derived',
                ],
                costMode: constants.costMode.ANY,
                supportsRefunds: true,
            },
            etfmCpc: {
                name: 'Avg. CPC',
                field: 'etfm_cpc',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                fractionSize: 3,
                help:
                    '<p>The average cost per click on an ad.</p>' +
                    '<p>The metric is calculated as the total cost divided by total amount of clicks.</p>',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                shown: true,
                costMode: constants.costMode.PUBLIC,
            },
            etfmCpm: {
                name: 'Avg. CPM',
                field: 'etfm_cpm',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                fractionSize: 3,
                help:
                    '<p>The average cost per thousand ad impressions. ' +
                    'Impression is counted whenever an ad is served to the user.</p>' +
                    '<p>The metric is calculated as the total cost divided by total amount ' +
                    'of impressions, multiplied by thousand.</p>',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                shown: true,
                costMode: constants.costMode.PUBLIC,
            },

            // Yesterday cost metrics
            yesterdayAtCost: {
                name: 'Actual Base Yesterday Spend',
                field: 'yesterday_at_cost',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                help:
                    'Amount that you have spent yesterday for promotion on specific ad group ' +
                    'including data spend and overspend.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                internal: 'zemauth.can_view_actual_costs',
                shown: 'zemauth.can_view_actual_costs',
                costMode: constants.costMode.ANY,
            },
            yesterdayEtfmCost: {
                name: 'Yesterday Spend',
                field: 'yesterday_etfm_cost',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                help:
                    'Amount that you have spent yesterday for promotion on specific ad group.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                shown: true,
                costMode: constants.costMode.PUBLIC,
            },

            // Traffic metrics
            clicks: {
                name: 'Clicks',
                field: 'clicks',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: true,
                help: 'The number of times a content ad has been clicked.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            impressions: {
                name: 'Impressions',
                field: 'impressions',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: true,
                totalRow: true,
                help: 'The number of times content ads have been displayed.',
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            ctr: {
                name: 'CTR',
                field: 'ctr',
                type: zemGridConstants.gridColumnTypes.PERCENT,
                shown: true,
                totalRow: true,
                help:
                    'The number of clicks divided by the number of impressions.',
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },

            // Optimization metrics
            totalSeconds: {
                name: 'Total Seconds',
                field: 'total_seconds',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: true,
                internal: false,
                help: 'Total time spend on site.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            bouncedVisits: {
                name: 'Bounced Visits',
                field: 'bounced_visits',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: true,
                internal: false,
                help:
                    'Number of visitors that navigate to more than one page on the site.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            nonBouncedVisits: {
                name: 'Non-Bounced Visits',
                field: 'non_bounced_visits',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: true,
                internal: false,
                help:
                    'Number of visitors that navigate to more than one page on the site.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            avgEtfmCostPerMinute: {
                name: 'Avg. Cost per Minute',
                field: 'avg_etfm_cost_per_minute',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                help:
                    '<p>The average cost per minute that visitors spent on your site. ' +
                    'Only visitors responding to an ad are included.</p>' +
                    '<p>Average cost per minute spent on site.</p>',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                goal: true,
                shown: true,
                costMode: constants.costMode.PUBLIC,
            },
            avgEtfmCostPerPageview: {
                name: 'Avg. Cost per Pageview',
                field: 'avg_etfm_cost_per_pageview',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                help:
                    '<p>The average cost per pageview on your site. ' +
                    'Only pageviews generated by visitors responding to an ad are included.</p>' +
                    '<p>The metric is calculated as total cost divided by the total amount of pageviews.</p>',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                goal: true,
                shown: true,
                costMode: constants.costMode.PUBLIC,
            },
            avgEtfmCostPerVisit: {
                name: 'Avg. Cost per Visit',
                field: 'avg_etfm_cost_per_visit',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                help:
                    '<p>The average cost per visit to your site. Only visits generated by ' +
                    'visitors responding to an ad are included.</p>' +
                    '<p>Visits are detected by your analytics software (Google Analytics or Adobe Analytics) as ' +
                    'opposed to clicks, which are detected by Zemanta. ' +
                    'They provide a better insight into the value of traffic sent by Zemanta.</p>' +
                    '<p>The metric is calculated as total cost divided by the total amount of visits.</p>',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                goal: true,
                shown: true,
                costMode: constants.costMode.PUBLIC,
            },
            avgEtfmCostPerNonBouncedVisit: {
                name: 'Avg. Cost per Non-Bounced Visit',
                field: 'avg_etfm_cost_per_non_bounced_visit',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                help:
                    '<p>The average cost per visitor that viewed more than one page in a session.</p>' +
                    '<p>A non bounced visit is more valuable because it indicates an interested visitor.</p>' +
                    '<p>The metric is calculated as the total cost divided by total amount of non-bounced visits.</p>',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                goal: true,
                shown: true,
                costMode: constants.costMode.PUBLIC,
            },
            avgEtfmCostPerNewVisitor: {
                name: 'Avg. Cost per New Visitor',
                field: 'avg_etfm_cost_per_new_visitor',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                help:
                    '<p>The average cost per new visitor. New visitor is a user that ' +
                    'visited your site for the first time.</p>' +
                    '<p>The metrics is calculated as total cost divided by total amount of new visitors.</p>',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                goal: true,
                shown: true,
                costMode: constants.costMode.PUBLIC,
            },
            avgEtfmCostPerUniqueUser: {
                name: 'Avg. Cost per Unique User',
                field: 'avg_etfm_cost_per_unique_user',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                help:
                    '<p>Cost per unique user. Calculated as (Total spend)/(Unique users)</p>',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                shown: true,
                costMode: constants.costMode.PUBLIC,
            },

            // Postclick Engagement Metrics
            percentNewUsers: {
                name: '% New Users',
                field: 'percent_new_users',
                type: zemGridConstants.gridColumnTypes.PERCENT,
                shown: true,
                internal: false,
                help:
                    'An estimate of first time visits during the selected date range.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            bounceRate: {
                name: 'Bounce Rate',
                field: 'bounce_rate',
                type: zemGridConstants.gridColumnTypes.PERCENT,
                shown: true,
                internal: false,
                help:
                    'Percentage of visits that resulted in only one page view.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            pvPerVisit: {
                name: 'Pageviews per Visit',
                field: 'pv_per_visit',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                fractionSize: 2,
                shown: true,
                internal: false,
                help: 'Average number of pageviews per visit.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            avgTos: {
                name: 'Time on Site',
                field: 'avg_tos',
                type: zemGridConstants.gridColumnTypes.SECONDS,
                shown: true,
                internal: false,
                help:
                    'Average time spent on site in seconds during the selected date range.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },

            // Postclick acquisition metrics
            visits: {
                name: 'Visits',
                field: 'visits',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: true,
                internal: false,
                help:
                    'Total number of sessions within a date range. A session is the period of time in which a user ' +
                    'is actively engaged with your site.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            uniqueUsers: {
                name: 'Unique Users',
                field: 'unique_users',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: true,
                internal: false,
                help:
                    'The total number of unique people who visited your site.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            newUsers: {
                name: 'New Users',
                field: 'new_users',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: true,
                internal: false,
                help:
                    'The total number of unique people who visited your site for the first time.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            returningUsers: {
                name: 'Returning Users',
                field: 'returning_users',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: true,
                internal: false,
                help:
                    'The total number of unique people who already visited your site in the past.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            clickDiscrepancy: {
                name: 'Click Discrepancy',
                field: 'click_discrepancy',
                type: zemGridConstants.gridColumnTypes.PERCENT,
                shown: true,
                internal: false,
                help:
                    'Clicks detected only by media source as a percentage of total clicks.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            pageviews: {
                name: 'Pageviews',
                field: 'pageviews',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: true,
                internal: false,
                help:
                    'Total number of pageviews made during the selected date range. A pageview is a view of ' +
                    'a single page. Repeated views are counted.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },

            // placeholders that are never shown
            conversionGoalsPlaceholder: {
                field: CONVERSION_GOALS_PLACEHOLDER,
                shown: false,
            },
            pixelsPlaceholder: {
                field: PIXELS_PLACEHOLDER,
                shown: false,
            },

            // conversions and cpa templates
            conversionCount: {
                type: zemGridConstants.gridColumnTypes.NUMBER,
                help: 'Number of completions of the conversion goal',
                shown: false,
                internal: false,
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            conversionRate: {
                type: zemGridConstants.gridColumnTypes.PERCENT,
                help: 'Conversion rate',
                shown: false,
                internal: false,
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            conversionCpa: {
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                help: 'Average cost per acquisition.',
                shown: false,
                internal: false,
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            conversionRoas: {
                type: zemGridConstants.gridColumnTypes.NUMBER,
                fractionSize: 2,
                help: 'Return on advertising spend.',
                shown: true,
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },

            // Video Metrics
            videoStart: {
                name: 'Video Start',
                field: 'video_start',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: true,
                help: 'Video Start.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            videoProgress3s: {
                name: 'Video Progress 3s',
                field: 'video_progress_3s',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: false,
                help: 'Video Progress 3s.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            videoFirstQuartile: {
                name: 'Video First Quartile',
                field: 'video_first_quartile',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: true,
                help: 'Video First Quartile.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            videoMidpoint: {
                name: 'Video Midpoint',
                field: 'video_midpoint',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: true,
                help: 'Video Midpoint.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            videoThirdQuartile: {
                name: 'Video Third Quartile',
                field: 'video_third_quartile',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: true,
                help: 'Video Third Quartile.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            videoComplete: {
                name: 'Video Complete',
                field: 'video_complete',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: true,
                help: 'Video Complete.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            videoStartPercent: {
                name: '% Video Start',
                field: 'video_start_percent',
                type: zemGridConstants.gridColumnTypes.PERCENT,
                fractionSize: 2,
                shown: true,
                help: '% Video Start.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            videoProgress3sPercent: {
                name: '% Video Progress 3s',
                field: 'video_progress_3s_percent',
                type: zemGridConstants.gridColumnTypes.PERCENT,
                fractionSize: 2,
                shown: false,
                help: '% Video Progress 3s.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            videoFirstQuartilePercent: {
                name: '% Video First Quartile',
                field: 'video_first_quartile_percent',
                type: zemGridConstants.gridColumnTypes.PERCENT,
                fractionSize: 2,
                shown: true,
                help: '% Video First Quartile.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            videoMidpointPercent: {
                name: '% Video Midpoint',
                field: 'video_midpoint_percent',
                type: zemGridConstants.gridColumnTypes.PERCENT,
                fractionSize: 2,
                shown: true,
                help: '% Video Midpoint.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            videoThirdQuartilePercent: {
                name: '% Video Third Quartile',
                field: 'video_third_quartile_percent',
                type: zemGridConstants.gridColumnTypes.PERCENT,
                fractionSize: 2,
                shown: true,
                help: '% Video Third Quartile.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            videoCompletePercent: {
                name: '% Video Complete',
                field: 'video_complete_percent',
                type: zemGridConstants.gridColumnTypes.PERCENT,
                fractionSize: 2,
                shown: true,
                help: '% Video Complete.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            videoEtfmCpv: {
                name: 'Avg. CPV',
                field: 'video_etfm_cpv',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                fractionSize: 3,
                help:
                    '<p>The average cost per 3 seconds video watch.</p>' +
                    '<p>The metric is calculated as the total cost divided by total amount of views.</p>',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                shown: true,
                costMode: constants.costMode.PUBLIC,
            },
            videoEtfmCpcv: {
                name: 'Avg. CPCV',
                field: 'video_etfm_cpcv',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                fractionSize: 3,
                help:
                    '<p>The average cost per completed video watch.</p>' +
                    '<p>The metric is calculated as the total cost divided by total amount of completed views.</p>',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
                shown: true,
                costMode: constants.costMode.PUBLIC,
            },
            placementId: {
                name: 'Placement Id',
                field: 'placement_id',
                order: true,
                type: zemGridConstants.gridColumnTypes.TEXT,
                shown: true,
            },
            placementType: {
                name: 'Placement Type',
                field: 'placement_type',
                order: true,
                type: zemGridConstants.gridColumnTypes.TEXT,
                shown: true,
            },
            publisher: {
                name: 'Publisher',
                field: 'publisher',
                order: true,
                type: zemGridConstants.gridColumnTypes.TEXT,
                shown: true,
            },

            // Viewability metrics
            mrc50Measurable: {
                name: 'Measurable Impressions',
                field: 'mrc50_measurable',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: true,
                help: 'Impressions for which we measured viewability.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            mrc50Viewable: {
                name: 'Viewable Impressions',
                field: 'mrc50_viewable',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: true,
                help:
                    'Number of impressions that were viewed by a person. Impression is counted as viewed when 50% of the ad is in view for 1 second.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            mrc50NonMeasurable: {
                name: 'Not-Measurable Impr.',
                field: 'mrc50_non_measurable',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: true,
                help:
                    'Impressions for which we couldn’t measure viewability. Calculated as Impressions - Measurable Impressions.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            mrc50NonViewable: {
                name: 'Not-Viewable Impressions',
                field: 'mrc50_non_viewable',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: true,
                help:
                    'Number of impressions that were not viewed by a person. Calculated as Measurable Impressions - Viewable Impressions',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            mrc50MeasurablePercent: {
                name: '% Measurable Impressions',
                field: 'mrc50_measurable_percent',
                type: 'percent',
                fractionSize: 2,
                shown: true,
                help:
                    'Percentage of impressions that were measurable. Calculated as 100 * Measurable impressions / Impressions.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            mrc50ViewablePercent: {
                name: '% Viewable Impressions',
                field: 'mrc50_viewable_percent',
                type: 'percent',
                fractionSize: 2,
                shown: true,
                help:
                    'Percentage of viewable impressions out of all measurable impressions. Calculated as 100 * Viewable Impressions / Measurable Impressions.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            mrc50ViewableDistribution: {
                name: 'Impression Distribution (Viewable)',
                field: 'mrc50_viewable_distribution',
                type: 'percent',
                fractionSize: 2,
                shown: true,
                help:
                    'Percentage of Viewable impressions out of all impressions. Calculated as 100 * Viewable Impressions / Impressions.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            mrc50NonMeasurableDistribution: {
                name: 'Impression Distribution (Not-Measurable)',
                field: 'mrc50_non_measurable_distribution',
                type: 'percent',
                fractionSize: 2,
                shown: true,
                help:
                    'Percentage of Not-Measurable impressions out of all impressions. Calculated as 100 * Not-Measurable Impressions / Impressions.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            mrc50NonViewableDistribution: {
                name: 'Impression Distribution (Not-Viewable)',
                field: 'mrc50_non_viewable_distribution',
                type: 'percent',
                fractionSize: 2,
                shown: true,
                help:
                    'Percentage of Not-Viewable impressions out of all impressions. Calculated as 100 * Not-Viewable Impressions / Impressions.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            etfmMrc50Vcpm: {
                name: 'Avg. VCPM',
                field: 'etfm_mrc50_vcpm',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                fractionSize: 3,
                shown: true,
                costMode: constants.costMode.PUBLIC,
                help:
                    'Average cost per thousand viewed impressions. Calculated as 1000 * Total.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            mrc100Measurable: {
                name: 'MRC100 Measurable Impressions',
                field: 'mrc100_measurable',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: ['zemauth.can_see_mrc100_metrics'],
                internal: 'zemauth.can_see_mrc100_metrics',
                help: 'Impressions for which we measured viewability.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            mrc100Viewable: {
                name: 'MRC100 Viewable Impressions',
                field: 'mrc100_viewable',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: ['zemauth.can_see_mrc100_metrics'],
                internal: 'zemauth.can_see_mrc100_metrics',
                help:
                    'Number of impressions that were viewed by a person. Impression is counted as viewed when 100% of the ad is in view for 1 second. ',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            mrc100NonMeasurable: {
                name: 'MRC100 Not-Measurable Impressions',
                field: 'mrc100_non_measurable',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: ['zemauth.can_see_mrc100_metrics'],
                internal: 'zemauth.can_see_mrc100_metrics',
                help:
                    'Impressions for which we couldn’t measure viewability. Calculated as Impressions - Measurable Impressions.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            mrc100NonViewable: {
                name: 'MRC100 Not-Viewable Impressions',
                field: 'mrc100_non_viewable',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: ['zemauth.can_see_mrc100_metrics'],
                internal: 'zemauth.can_see_mrc100_metrics',
                help:
                    'Number of impressions that were not viewed by a person. Calculated as Measurable Impressions - Viewable Impressions.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            mrc100MeasurablePercent: {
                name: '% MRC100 Measurable Impressions',
                field: 'mrc100_measurable_percent',
                type: 'percent',
                fractionSize: 2,
                shown: ['zemauth.can_see_mrc100_metrics'],
                internal: 'zemauth.can_see_mrc100_metrics',
                help:
                    'Percentage of impressions that were measurable. Calculated as 100 * Measurable impressions / Impressions.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            mrc100ViewablePercent: {
                name: '% MRC100 Viewable Impressions',
                field: 'mrc100_viewable_percent',
                type: 'percent',
                fractionSize: 2,
                shown: ['zemauth.can_see_mrc100_metrics'],
                internal: 'zemauth.can_see_mrc100_metrics',
                help:
                    'Percentage of viewable impressions out of all measurable impressions. Calculated as 100 * Viewable Impressions / Measurable Impressions.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            mrc100ViewableDistribution: {
                name: 'MRC100 Impression Distribution (Viewable)',
                field: 'mrc100_viewable_distribution',
                type: 'percent',
                fractionSize: 2,
                shown: ['zemauth.can_see_mrc100_metrics'],
                internal: 'zemauth.can_see_mrc100_metrics',
                help:
                    'Percentage of Viewable impressions out of all impressions. Calculated as 100 * Viewable Impressions / Impressions.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            mrc100NonMeasurableDistribution: {
                name: 'MRC100 Impression Distribution (Not-Measurable)',
                field: 'mrc100_non_measurable_distribution',
                type: 'percent',
                fractionSize: 2,
                shown: ['zemauth.can_see_mrc100_metrics'],
                internal: 'zemauth.can_see_mrc100_metrics',
                help:
                    'Percentage of Not-Measurable impressions out of all impressions. Calculated as 100 * Not-Measurable Impressions / Impressions.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            mrc100NonViewableDistribution: {
                name: 'MRC100 Impression Distribution (Not-Viewable)',
                field: 'mrc100_non_viewable_distribution',
                type: 'percent',
                fractionSize: 2,
                shown: ['zemauth.can_see_mrc100_metrics'],
                internal: 'zemauth.can_see_mrc100_metrics',
                help:
                    'Percentage of Not-Viewable impressions out of all impressions. Calculated as 100 * Not-Viewable Impressions / Impressions.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            etfmMrc100Vcpm: {
                name: 'Avg. MRC100 VCPM',
                field: 'etfm_mrc100_vcpm',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                fractionSize: 3,
                shown: ['zemauth.can_see_mrc100_metrics'],
                costMode: constants.costMode.PUBLIC,
                internal: 'zemauth.can_see_mrc100_metrics',
                help:
                    'Average cost per thousand viewed impressions. Calculated as 1000 * Total.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            vast4Measurable: {
                name: 'Video Measurable Impressions',
                field: 'vast4_measurable',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: ['zemauth.can_see_vast4_metrics'],
                internal: 'zemauth.can_see_vast4_metrics',
                help: 'Impressions for which we measured viewability.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            vast4Viewable: {
                name: 'Video Viewable Impressions',
                field: 'vast4_viewable',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: ['zemauth.can_see_vast4_metrics'],
                internal: 'zemauth.can_see_vast4_metrics',
                help: 'Number of impressions that were viewed by a person.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            vast4NonMeasurable: {
                name: 'Video Not-Measurable',
                field: 'vast4_non_measurable',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: ['zemauth.can_see_vast4_metrics'],
                internal: 'zemauth.can_see_vast4_metrics',
                help:
                    'Impressions for which we couldn’t measure viewability. Calculated as Impressions - Measurable Impressions.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            vast4NonViewable: {
                name: 'Video Not-Viewable',
                field: 'vast4_non_viewable',
                type: zemGridConstants.gridColumnTypes.NUMBER,
                shown: ['zemauth.can_see_vast4_metrics'],
                internal: 'zemauth.can_see_vast4_metrics',
                help:
                    'Number of impressions that were not viewed by a person. Calculated as Measurable Impressions - Viewable Impressions.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            vast4MeasurablePercent: {
                name: '% Video Measurable Impressions',
                field: 'vast4_measurable_percent',
                type: 'percent',
                fractionSize: 2,
                shown: ['zemauth.can_see_vast4_metrics'],
                internal: 'zemauth.can_see_vast4_metrics',
                help:
                    'Percentage of impressions that were measurable. Calculated as 100 * Measurable impressions / Impressions.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            vast4ViewablePercent: {
                name: '% Video Viewable Impressions',
                field: 'vast4_viewable_percent',
                type: 'percent',
                fractionSize: 2,
                shown: ['zemauth.can_see_vast4_metrics'],
                internal: 'zemauth.can_see_vast4_metrics',
                help:
                    'Percentage of viewable impressions out of all measurable impressions. Calculated as 100 * Viewable Impressions / Measurable Impressions.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            vast4ViewableDistribution: {
                name: 'Video Impression Distribution (Viewable)',
                field: 'vast4_viewable_distribution',
                type: 'percent',
                fractionSize: 2,
                shown: ['zemauth.can_see_vast4_metrics'],
                internal: 'zemauth.can_see_vast4_metrics',
                help:
                    'Percentage of Viewable impressions out of all impressions. Calculated as 100 * Viewable Impressions / Impressions.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            vast4NonMeasurableDistribution: {
                name: 'Video Impression Distribution (Not-Measurable)',
                field: 'vast4_non_measurable_distribution',
                type: 'percent',
                fractionSize: 2,
                shown: ['zemauth.can_see_vast4_metrics'],
                internal: 'zemauth.can_see_vast4_metrics',
                help:
                    'Percentage of Not-Measurable impressions out of all impressions. Calculated as 100 * Not-Measurable Impressions / Impressions.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            vast4NonViewableDistribution: {
                name: 'Video Impression Distribution (Not-Viewable)',
                field: 'vast4_non_viewable_distribution',
                type: 'percent',
                fractionSize: 2,
                shown: ['zemauth.can_see_vast4_metrics'],
                internal: 'zemauth.can_see_vast4_metrics',
                help:
                    'Percentage of Not-Viewable impressions out of all impressions. Calculated as 100 * Not-Viewable Impressions / Impressions.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
            etfmVast4Vcpm: {
                name: 'Avg. VAST4 VCPM',
                field: 'etfm_vast4_vcpm',
                type: zemGridConstants.gridColumnTypes.CURRENCY,
                fractionSize: 3,
                shown: ['zemauth.can_see_vast4_metrics'],
                costMode: constants.costMode.PUBLIC,
                internal: 'zemauth.can_see_vast4_metrics',
                help:
                    'Average cost per thousand viewed impressions. Calculated as 1000 * Total.',
                totalRow: true,
                order: true,
                initialOrder: zemGridConstants.gridColumnOrder.DESC,
            },
        };

        // ///////////////////////////////////////////////////////////////////////////////////////////////////
        //  COLUMN BRANDING - provide properties that depends on breakdown/level (e.g. name)
        //
        var NAME_COLUMN_BRANDING = {};
        NAME_COLUMN_BRANDING[constants.breakdown.ACCOUNT] = {
            name: 'Account',
            help: 'A partner account.',
        };
        NAME_COLUMN_BRANDING[constants.breakdown.CAMPAIGN] = {
            name: 'Campaign',
            help: 'Name of the campaign.',
        };
        NAME_COLUMN_BRANDING[constants.breakdown.AD_GROUP] = {
            name: 'Ad Group',
            help: 'Name of the ad group.',
        };
        NAME_COLUMN_BRANDING[constants.breakdown.CONTENT_AD] = {
            name: 'Content Ad',
            help:
                'The creative title/name/headline of a content ad. The link to landing page includes tracking codes.',
        };
        NAME_COLUMN_BRANDING[constants.breakdown.MEDIA_SOURCE] = {
            name: 'Media Source',
            help: 'A media source where your content is being promoted.',
        };
        NAME_COLUMN_BRANDING[constants.breakdown.PUBLISHER] = {
            name: 'Publisher',
            help: 'A publisher where your content is being promoted.',
        };
        NAME_COLUMN_BRANDING[constants.breakdown.PLACEMENT] = {
            name: 'Placement',
            help: 'A placement where your content is being promoted.',
        };
        NAME_COLUMN_BRANDING[constants.breakdown.COUNTRY] = {
            name: 'Country',
            help: '',
        };
        NAME_COLUMN_BRANDING[constants.breakdown.STATE] = {
            name: 'State / Region',
            help: '',
        };
        NAME_COLUMN_BRANDING[constants.breakdown.DMA] = {
            name: 'DMA',
            help: '',
        };
        NAME_COLUMN_BRANDING[constants.breakdown.DEVICE] = {
            name: 'Device',
            help: '',
        };
        NAME_COLUMN_BRANDING[constants.breakdown.ENVIRONMENT] = {
            name: 'Environment',
            help: '',
        };
        NAME_COLUMN_BRANDING[constants.breakdown.OPERATING_SYSTEM] = {
            name: 'Operating System',
            help: '',
        };
        NAME_COLUMN_BRANDING[constants.breakdown.BROWSER] = {
            name: 'Browser',
            help: '',
        };
        NAME_COLUMN_BRANDING[constants.breakdown.CONNECTION_TYPE] = {
            name: 'Connection Type',
            help: '',
        };

        var STATUS_COLUMN_BRANDING = {};
        STATUS_COLUMN_BRANDING[constants.breakdown.ACCOUNT] = {
            name: 'Status',
            help:
                'Status of an account (enabled or paused). An account is paused only if all its campaigns ' +
                'are paused too; otherwise the account is enabled.',
        };
        STATUS_COLUMN_BRANDING[constants.breakdown.CAMPAIGN] = {
            name: 'Status',
            help:
                'Status of a campaign (enabled or paused). A campaign is paused only if all its ad groups ' +
                'are paused too; otherwise, the campaign is enabled.',
        };
        STATUS_COLUMN_BRANDING[constants.breakdown.AD_GROUP] = {
            name: 'Status',
            help: 'Status of an ad group (enabled or paused).',
        };
        STATUS_COLUMN_BRANDING[constants.breakdown.CONTENT_AD] = {
            name: 'Status',
            help: 'Status of an content ad (enabled or paused).',
        };
        STATUS_COLUMN_BRANDING[constants.breakdown.MEDIA_SOURCE] = {
            name: 'Status',
            help: 'Status of a particular media source (enabled or paused).',
        };
        STATUS_COLUMN_BRANDING[constants.breakdown.PUBLISHER] = {
            name: 'Status',
            help: 'Blacklisted status of a publisher.',
        };
        STATUS_COLUMN_BRANDING[constants.breakdown.PLACEMENT] = {
            name: 'Status',
            help: 'Blacklisted status of a placement.',
        };

        var STATE_COLUMN_BRANDING = {};
        STATE_COLUMN_BRANDING[constants.breakdown.AD_GROUP] = {
            name: '\u25CF',
            help: 'A setting for enabling and pausing Ad Groups.',
        };
        STATE_COLUMN_BRANDING[constants.breakdown.CONTENT_AD] = {
            name: '\u25CF',
            help: 'A setting for enabling and pausing content ads.',
        };
        STATE_COLUMN_BRANDING[constants.breakdown.MEDIA_SOURCE] = {
            name: '\u25CF',
            help: 'A setting for enabling and pausing media sources.',
        };

        // ///////////////////////////////////////////////////////////////////////////////////////////////////
        //  COMMON COLUMN GROUPS
        //

        // Permanent columns - always present and can't be hidden
        var PERMANENT_COLUMNS_GROUP = [
            COLUMNS.actions,
            COLUMNS.state,
            COLUMNS.name,
            COLUMNS.placementType,
            COLUMNS.publisher,
            COLUMNS.exchange,
            COLUMNS.status,
            COLUMNS.submissionStatus,
            COLUMNS.performance,
            COLUMNS.bidModifier,
        ];

        // Default columns - columns present by default (non permanent can be hidden)
        var DEFAULT_COLUMNS_GROUP = PERMANENT_COLUMNS_GROUP.concat([
            COLUMNS.imageUrls,
            COLUMNS.yesterdayEtfmCost,
            COLUMNS.clicks,
            COLUMNS.etfmCpc,
        ]);

        var ACCOUNT_MANAGEMENT_GROUP = [
            COLUMNS.agency,
            COLUMNS.accountType,
            COLUMNS.defaultSalesRepresentative,
            COLUMNS.defaultCsRepresentative,
            COLUMNS.obSalesRepresentative,
            COLUMNS.obAccountManager,
            COLUMNS.defaultAccountManager,
            COLUMNS.salesforceUrl,
        ];

        var MANAGEMENT_GROUP = [
            COLUMNS.agencyId,
            COLUMNS.accountId,
            COLUMNS.campaignId,
            COLUMNS.campaignType,
            COLUMNS.campaignManager,
            COLUMNS.adGroupId,
            COLUMNS.contentAdId,
            COLUMNS.amplifyAdId,
            COLUMNS.sourceId,
            COLUMNS.sourceSlug,
            COLUMNS.sspdUrl,
        ].concat(ACCOUNT_MANAGEMENT_GROUP);

        var SOURCE_GROUP = [COLUMNS.supplyDashUrl];

        var PUBLISHER_GROUP = [COLUMNS.domain, COLUMNS.domainLink];

        var PLACEMENT_GROUP = [COLUMNS.placementId];

        var CONTENT_GROUP = [
            COLUMNS.imageUrls,
            COLUMNS.urlLink,
            COLUMNS.displayUrl,
            COLUMNS.brandName,
            COLUMNS.description,
            COLUMNS.callToAction,
            COLUMNS.adType,
            COLUMNS.creativeSize,
            COLUMNS.label,
            COLUMNS.impressionTrackers,
            COLUMNS.uploadTime,
            COLUMNS.batchId,
            COLUMNS.batchName,
            COLUMNS.amplifyLivePreview,
        ];

        var COSTS_GROUP = [
            COLUMNS.yesterdayAtCost,
            COLUMNS.yesterdayEtfmCost,
            COLUMNS.mediaCost,
            COLUMNS.bMediaCost,
            COLUMNS.eMediaCost,
            COLUMNS.dataCost,
            COLUMNS.bDataCost,
            COLUMNS.eDataCost,
            COLUMNS.serviceFee,
            COLUMNS.licenseFee,
            COLUMNS.margin,
            COLUMNS.atCost,
            COLUMNS.btCost,
            COLUMNS.etCost,
            COLUMNS.etfCost,
            COLUMNS.etfmCost,
            COLUMNS.dailyBudgetSetting,
        ];

        var TRAFFIC_ACQUISITION_GROUP = [
            COLUMNS.impressions,
            COLUMNS.clicks,
            COLUMNS.ctr,
            COLUMNS.etfmCpc,
            COLUMNS.etfmCpm,
        ];

        var MRC50_VIEWABILITY_METRICS_GROUP = [
            COLUMNS.mrc50Measurable,
            COLUMNS.mrc50Viewable,
            COLUMNS.mrc50NonMeasurable,
            COLUMNS.mrc50NonViewable,
            COLUMNS.mrc50MeasurablePercent,
            COLUMNS.mrc50ViewablePercent,
            COLUMNS.mrc50ViewableDistribution,
            COLUMNS.mrc50NonMeasurableDistribution,
            COLUMNS.mrc50NonViewableDistribution,
            COLUMNS.etfmMrc50Vcpm,
        ];

        var MRC100_VIEWABILITY_METRICS_GROUP = [
            COLUMNS.mrc100Measurable,
            COLUMNS.mrc100Viewable,
            COLUMNS.mrc100NonMeasurable,
            COLUMNS.mrc100NonViewable,
            COLUMNS.mrc100MeasurablePercent,
            COLUMNS.mrc100ViewablePercent,
            COLUMNS.mrc100ViewableDistribution,
            COLUMNS.mrc100NonMeasurableDistribution,
            COLUMNS.mrc100NonViewableDistribution,
            COLUMNS.etfmMrc100Vcpm,
        ];

        var VAST4_VIEWABILITY_METRICS_GROUP = [
            COLUMNS.vast4Measurable,
            COLUMNS.vast4Viewable,
            COLUMNS.vast4NonMeasurable,
            COLUMNS.vast4NonViewable,
            COLUMNS.vast4MeasurablePercent,
            COLUMNS.vast4ViewablePercent,
            COLUMNS.vast4ViewableDistribution,
            COLUMNS.vast4NonMeasurableDistribution,
            COLUMNS.vast4NonViewableDistribution,
            COLUMNS.etfmVast4Vcpm,
        ];

        var AUDIENCE_METRICS_GROUP = [
            COLUMNS.visits,
            COLUMNS.uniqueUsers,
            COLUMNS.newUsers,
            COLUMNS.returningUsers,
            COLUMNS.percentNewUsers,
            COLUMNS.clickDiscrepancy,
            COLUMNS.pageviews,
            COLUMNS.pvPerVisit,
            COLUMNS.bouncedVisits,
            COLUMNS.nonBouncedVisits,
            COLUMNS.bounceRate,
            COLUMNS.totalSeconds,
            COLUMNS.avgTos,
            COLUMNS.avgEtfmCostPerVisit,
            COLUMNS.avgEtfmCostPerNewVisitor,
            COLUMNS.avgEtfmCostPerPageview,
            COLUMNS.avgEtfmCostPerNonBouncedVisit,
            COLUMNS.avgEtfmCostPerMinute,
            COLUMNS.avgEtfmCostPerUniqueUser,
        ];

        var PIXELS_GROUP = [COLUMNS.pixelsPlaceholder];

        var CONVERSION_GOALS_GROUP = [COLUMNS.conversionGoalsPlaceholder];

        var VIDEO_METRICS_GROUP = [
            COLUMNS.videoStart,
            COLUMNS.videoProgress3s,
            COLUMNS.videoFirstQuartile,
            COLUMNS.videoMidpoint,
            COLUMNS.videoThirdQuartile,
            COLUMNS.videoComplete,
            COLUMNS.videoEtfmCpv,
            COLUMNS.videoEtfmCpcv,
            COLUMNS.videoStartPercent,
            COLUMNS.videoProgress3sPercent,
            COLUMNS.videoFirstQuartilePercent,
            COLUMNS.videoMidpointPercent,
            COLUMNS.videoThirdQuartilePercent,
            COLUMNS.videoCompletePercent,
        ];

        var METRICS_GROUP = [].concat(
            COSTS_GROUP,
            TRAFFIC_ACQUISITION_GROUP,
            MRC50_VIEWABILITY_METRICS_GROUP,
            MRC100_VIEWABILITY_METRICS_GROUP,
            VAST4_VIEWABILITY_METRICS_GROUP,
            AUDIENCE_METRICS_GROUP,
            PIXELS_GROUP,
            CONVERSION_GOALS_GROUP,
            VIDEO_METRICS_GROUP
        );

        // //////////////////////////////////////////////////////////////////////////////////////////////////
        //  COLUMNS CONFIGURATION (order, availability, ...)
        //

        // Sets order of columns (this collection is used for creation)
        var COLUMNS_ORDERED = [].concat(
            PERMANENT_COLUMNS_GROUP,
            MANAGEMENT_GROUP,
            CONTENT_GROUP,
            SOURCE_GROUP,
            PUBLISHER_GROUP,
            PLACEMENT_GROUP,
            METRICS_GROUP
        );

        // Configure special column properties
        PERMANENT_COLUMNS_GROUP.forEach(function(column) {
            column.permanent = true;
        });
        DEFAULT_COLUMNS_GROUP.forEach(function(column) {
            column.default = true;
        });

        // Exceptions object
        COLUMNS_ORDERED.forEach(function(column) {
            column.exceptions = {
                levels: undefined, // levels where this column is available; defaults to ALL
                breakdowns: undefined, // breakdowns where this column is available; defaults to ALL
                breakdownBaseLevelOnly: false, // column only available on base level (level 1)
                custom: [], // custom exceptions -> level/breakdown pairs; overwrites previous properties
            };
        });

        // Configuration (availability based on breakdown)
        configureBreakdownExceptions(ACCOUNT_MANAGEMENT_GROUP, [
            constants.breakdown.ACCOUNT,
        ]);
        configureBreakdownExceptions(
            [COLUMNS.campaignType, COLUMNS.campaignManager],
            [constants.breakdown.CAMPAIGN]
        );
        configureBreakdownExceptions(CONTENT_GROUP, [
            constants.breakdown.CONTENT_AD,
        ]);
        configureBreakdownExceptions(SOURCE_GROUP, [
            constants.breakdown.MEDIA_SOURCE,
        ]);
        configureBreakdownExceptions(PUBLISHER_GROUP, [
            constants.breakdown.PUBLISHER,
            constants.breakdown.PLACEMENT,
        ]);
        configureBreakdownExceptions(PLACEMENT_GROUP, [
            constants.breakdown.PLACEMENT,
        ]);

        // Exceptions (content ad amplify live preview - only visible on ad group content ad tab)
        COLUMNS.amplifyLivePreview.exceptions.levels = [
            constants.level.AD_GROUPS,
        ];
        COLUMNS.amplifyLivePreview.exceptions.breakdowns = [
            constants.breakdown.CONTENT_AD,
        ];
        COLUMNS.amplifyLivePreview.exceptions.breakdownBaseLevelOnly = true;

        // Exceptions (content ad amplify id - only visible on ad group content ad tab)
        COLUMNS.amplifyAdId.exceptions.levels = [constants.level.AD_GROUPS];
        COLUMNS.amplifyAdId.exceptions.breakdowns = [
            constants.breakdown.CONTENT_AD,
        ];
        COLUMNS.amplifyAdId.exceptions.breakdownBaseLevelOnly = true;

        // Exceptions (state - not yet supported everywhere, only available on base level)
        COLUMNS.state.exceptions.breakdowns = [
            constants.breakdown.AD_GROUP,
            constants.breakdown.CONTENT_AD,
        ];
        COLUMNS.state.exceptions.breakdownBaseLevelOnly = true;
        // State selector is only shown on MEDIA_SOURCE breakdown on AD_GROUPS level
        COLUMNS.state.exceptions.custom.push({
            level: constants.level.AD_GROUPS,
            breakdown: constants.breakdown.MEDIA_SOURCE,
            shown: true,
        }); // eslint-disable-line max-len

        // Exceptions (actions - on media source breakdown only on ad group level)
        COLUMNS.actions.exceptions.breakdowns = [
            constants.breakdown.ACCOUNT,
            constants.breakdown.CAMPAIGN,
            constants.breakdown.AD_GROUP,
            constants.breakdown.CONTENT_AD,
        ];
        COLUMNS.actions.exceptions.custom.push({
            level: constants.level.ACCOUNTS,
            breakdown: constants.breakdown.PUBLISHER,
            shown: true,
        });
        COLUMNS.actions.exceptions.custom.push({
            level: constants.level.CAMPAIGNS,
            breakdown: constants.breakdown.PUBLISHER,
            shown: true,
        });
        COLUMNS.actions.exceptions.custom.push({
            level: constants.level.AD_GROUPS,
            breakdown: constants.breakdown.PUBLISHER,
            shown: true,
        });
        COLUMNS.actions.exceptions.custom.push({
            level: constants.level.ACCOUNTS,
            breakdown: constants.breakdown.PLACEMENT,
            shown: true,
        });
        COLUMNS.actions.exceptions.custom.push({
            level: constants.level.CAMPAIGNS,
            breakdown: constants.breakdown.PLACEMENT,
            shown: true,
        });
        COLUMNS.actions.exceptions.custom.push({
            level: constants.level.AD_GROUPS,
            breakdown: constants.breakdown.PLACEMENT,
            shown: true,
        });
        COLUMNS.actions.exceptions.custom.push({
            level: constants.level.AD_GROUPS,
            breakdown: constants.breakdown.MEDIA_SOURCE,
            shown: true,
        });

        // Exceptions (submission status - only shown on AD_GROUPS level for CONTENT_AD breakdown)
        COLUMNS.submissionStatus.exceptions.breakdowns = [
            constants.breakdown.CONTENT_AD,
        ];
        COLUMNS.submissionStatus.exceptions.levels = [
            constants.level.AD_GROUPS,
        ];

        COLUMNS.exchange.exceptions.breakdowns = [
            constants.breakdown.PUBLISHER,
            constants.breakdown.PLACEMENT,
        ];

        COLUMNS.placementId.exceptions.breakdowns = [
            constants.breakdown.PLACEMENT,
        ];

        COLUMNS.placementType.exceptions.breakdowns = [
            constants.breakdown.PLACEMENT,
        ];

        COLUMNS.publisher.exceptions.breakdowns = [
            constants.breakdown.PLACEMENT,
        ];

        // Exceptions (performance - not shown on ALL_ACCOUNTS level and on ACCOUNT - MEDIA SOURCES)
        COLUMNS.performance.exceptions.levels = [
            constants.level.ACCOUNTS,
            constants.level.CAMPAIGNS,
            constants.level.AD_GROUPS,
        ]; // eslint-disable-line max-len
        COLUMNS.performance.exceptions.custom.push({
            level: constants.level.ACCOUNTS,
            breakdown: constants.breakdown.MEDIA_SOURCE,
            shown: false,
        }); // eslint-disable-line max-len
        COLUMNS.performance.exceptions.custom.push({
            level: constants.level.ACCOUNTS,
            breakdown: constants.breakdown.PUBLISHER,
            shown: false,
        }); // eslint-disable-line max-len
        COLUMNS.performance.exceptions.custom.push({
            level: constants.level.ACCOUNTS,
            breakdown: constants.breakdown.PLACEMENT,
            shown: false,
        }); // eslint-disable-line max-len

        // Exceptions (media source status column - shown only on Ad Group level)
        COLUMNS.status.exceptions.breakdowns = [
            constants.breakdown.ACCOUNT,
            constants.breakdown.CAMPAIGN,
            constants.breakdown.AD_GROUP,
            constants.breakdown.CONTENT_AD,
            constants.breakdown.MEDIA_SOURCE,
            constants.breakdown.MEDIA_SOURCE,
            constants.breakdown.PUBLISHER,
            constants.breakdown.PLACEMENT,
        ]; // eslint-disable-line max-len
        COLUMNS.status.exceptions.custom.push({
            level: constants.level.ALL_ACCOUNTS,
            breakdown: constants.breakdown.MEDIA_SOURCE,
            shown: false,
        }); // eslint-disable-line max-len
        COLUMNS.status.exceptions.custom.push({
            level: constants.level.ACCOUNTS,
            breakdown: constants.breakdown.MEDIA_SOURCE,
            shown: false,
        }); // eslint-disable-line max-len
        COLUMNS.status.exceptions.custom.push({
            level: constants.level.CAMPAIGNS,
            breakdown: constants.breakdown.MEDIA_SOURCE,
            shown: false,
        }); // eslint-disable-line max-len

        // Exceptions (supply dash url - only shown on AD_GROUPS level on base row level)
        COLUMNS.supplyDashUrl.exceptions.levels = [constants.level.AD_GROUPS];
        COLUMNS.supplyDashUrl.exceptions.breakdownBaseLevelOnly = true;

        // Exceptions (source editable fields)
        COLUMNS.dailyBudgetSetting.exceptions = {
            levels: [constants.level.AD_GROUPS],
            breakdowns: [constants.breakdown.MEDIA_SOURCE],
            breakdownBaseLevelOnly: true,
            custom: [], // custom exceptions -> level/breakdown pairs; overwrites previous properties
        };

        COLUMNS.bidModifier.exceptions.breakdowns = [
            constants.breakdown.CONTENT_AD,
            constants.breakdown.COUNTRY,
            constants.breakdown.STATE,
            constants.breakdown.DMA,
            constants.breakdown.DEVICE,
            constants.breakdown.ENVIRONMENT,
            constants.breakdown.OPERATING_SYSTEM,
            constants.breakdown.PUBLISHER,
            constants.breakdown.PLACEMENT,
            constants.breakdown.MEDIA_SOURCE,
            constants.breakdown.BROWSER,
            constants.breakdown.CONNECTION_TYPE,
        ];
        COLUMNS.bidModifier.exceptions.levels = [constants.level.AD_GROUPS];
        COLUMNS.bidModifier.exceptions.breakdownBaseLevelOnly = true;

        // Exceptions (id columns)
        COLUMNS.agencyId.exceptions.breakdowns = [
            constants.breakdown.ACCOUNT,
            constants.breakdown.CAMPAIGN,
            constants.breakdown.AD_GROUP,
            constants.breakdown.CONTENT_AD,
            constants.breakdown.COUNTRY,
            constants.breakdown.STATE,
            constants.breakdown.DMA,
            constants.breakdown.DEVICE,
            constants.breakdown.ENVIRONMENT,
            constants.breakdown.OPERATING_SYSTEM,
            constants.breakdown.BROWSER,
            constants.breakdown.CONNECTION_TYPE,
        ]; // eslint-disable-line max-len
        COLUMNS.accountId.exceptions.breakdowns = [
            constants.breakdown.ACCOUNT,
            constants.breakdown.CAMPAIGN,
            constants.breakdown.AD_GROUP,
            constants.breakdown.CONTENT_AD,
            constants.breakdown.COUNTRY,
            constants.breakdown.STATE,
            constants.breakdown.DMA,
            constants.breakdown.DEVICE,
            constants.breakdown.ENVIRONMENT,
            constants.breakdown.OPERATING_SYSTEM,
            constants.breakdown.BROWSER,
            constants.breakdown.CONNECTION_TYPE,
        ]; // eslint-disable-line max-len
        COLUMNS.campaignId.exceptions.breakdowns = [
            constants.breakdown.CAMPAIGN,
            constants.breakdown.AD_GROUP,
            constants.breakdown.CONTENT_AD,
            constants.breakdown.COUNTRY,
            constants.breakdown.STATE,
            constants.breakdown.DMA,
            constants.breakdown.DEVICE,
            constants.breakdown.ENVIRONMENT,
            constants.breakdown.OPERATING_SYSTEM,
            constants.breakdown.BROWSER,
            constants.breakdown.CONNECTION_TYPE,
        ]; // eslint-disable-line max-len
        COLUMNS.adGroupId.exceptions.breakdowns = [
            constants.breakdown.AD_GROUP,
            constants.breakdown.CONTENT_AD,
            constants.breakdown.COUNTRY,
            constants.breakdown.STATE,
            constants.breakdown.DMA,
            constants.breakdown.DEVICE,
            constants.breakdown.ENVIRONMENT,
            constants.breakdown.OPERATING_SYSTEM,
            constants.breakdown.BROWSER,
            constants.breakdown.CONNECTION_TYPE,
        ];
        COLUMNS.contentAdId.exceptions.breakdowns = [
            constants.breakdown.CONTENT_AD,
        ];
        COLUMNS.sourceId.exceptions.breakdowns = [
            constants.breakdown.MEDIA_SOURCE,
            constants.breakdown.PUBLISHER,
            constants.breakdown.PLACEMENT,
        ];
        COLUMNS.sourceSlug.exceptions.breakdowns = [
            constants.breakdown.MEDIA_SOURCE,
            constants.breakdown.PUBLISHER,
            constants.breakdown.PLACEMENT,
        ];
        COLUMNS.sspdUrl.exceptions.breakdowns = [
            constants.breakdown.ACCOUNT,
            constants.breakdown.CAMPAIGN,
            constants.breakdown.AD_GROUP,
            constants.breakdown.CONTENT_AD,
        ];

        function configureBreakdownExceptions(columns, breakdowns) {
            columns.forEach(function(column) {
                column.exceptions.breakdowns = breakdowns;
            });
        }

        // ///////////////////////////////////////////////////////////////////////////////////////////////////
        //  COLUMN CATEGORIES
        //
        var CATEGORIES = [
            {
                name: 'Management',
                columns: [].concat(MANAGEMENT_GROUP),
            },
            {
                name: 'Content',
                columns: CONTENT_GROUP,
            },
            {
                name: 'Media Source',
                columns: SOURCE_GROUP,
            },
            {
                name: 'Publisher',
                columns: PUBLISHER_GROUP,
            },
            {
                name: 'Placement',
                columns: PLACEMENT_GROUP,
            },
            {
                name: 'Costs',
                columns: COSTS_GROUP,
            },
            {
                name: 'Traffic Acquisition',
                columns: TRAFFIC_ACQUISITION_GROUP,
            },
            {
                name: 'Viewability',
                columns: MRC50_VIEWABILITY_METRICS_GROUP,
            },
            {
                name: 'MRC100 Viewability',
                columns: MRC100_VIEWABILITY_METRICS_GROUP,
                isNewFeature: true,
            },
            {
                name: 'Audience Metrics',
                columns: AUDIENCE_METRICS_GROUP,
            },
            {
                name: CategoryName.PIXELS,
                description: 'Choose conversion window in days.',
                columns: PIXELS_GROUP,
            },
            {
                name: 'Google & Adobe Analytics Goals',
                columns: CONVERSION_GOALS_GROUP,
            },
            {
                name: 'Video Metrics',
                columns: VIDEO_METRICS_GROUP,
            },
            {
                name: 'Video Viewability',
                columns: VAST4_VIEWABILITY_METRICS_GROUP,
                isNewFeature: true,
            },
        ];

        // ///////////////////////////////////////////////////////////////////////////////////////////////////
        // Service functions
        //

        function checkPermissions(columns, breakdown) {
            var activeAccount = zemNavigationNewService.getActiveAccount();
            // Go trough all columns and convert permissions to boolean, when needed
            columns.forEach(function(column) {
                var columnPermissions = column.shown;
                if (column.shown instanceof Array) {
                    var item = column.shown.find(function(item) {
                        return (
                            typeof item === 'object' &&
                            item.breakdowns &&
                            item.breakdowns.indexOf(breakdown) >= 0
                        );
                    });
                    if (item) {
                        columnPermissions = item.permissions;
                    }
                }

                column.internal = zemUtils.convertPermission(
                    column.internal,
                    zemAuthStore.isPermissionInternal.bind(zemAuthStore)
                );

                if (column.shownForEntity) {
                    if (activeAccount) {
                        column.shown = zemAuthStore.hasPermissionOn(
                            activeAccount.data.agencyId,
                            activeAccount.id,
                            column.shownForEntity
                        );
                    } else {
                        column.shown = zemAuthStore.hasPermissionOnAnyEntity(
                            column.shownForEntity
                        );
                    }
                } else {
                    column.shown = zemUtils.convertPermission(
                        columnPermissions,
                        zemAuthStore.hasPermission.bind(zemAuthStore)
                    );
                }
            });
        }

        function adjustOrder(columns, breakdowns) {
            // status not orderable on publisher and placement tabs
            if (
                breakdowns.indexOf(constants.breakdown.PUBLISHER) >= 0 ||
                breakdowns.indexOf(constants.breakdown.PLACEMENT) >= 0
            ) {
                columns.forEach(function(column) {
                    if (column.field === COLUMNS.status.field) {
                        column.order = false;
                    }
                });
            }
        }

        function brandColumns(columns, breakdown) {
            function findColumn(column) {
                return columns.filter(function(c) {
                    return column.field === c.field;
                })[0];
            }

            var nameColumn = findColumn(COLUMNS.name);
            nameColumn.name = NAME_COLUMN_BRANDING[breakdown].name;
            nameColumn.help = NAME_COLUMN_BRANDING[breakdown].help;

            var statusColumn = findColumn(COLUMNS.status);
            if (statusColumn) {
                statusColumn.name = STATUS_COLUMN_BRANDING[breakdown].name;
                statusColumn.help = STATUS_COLUMN_BRANDING[breakdown].help;
            }
        }

        function getColumns(level, breakdowns) {
            return COLUMNS_ORDERED.filter(function(column) {
                var result = true;

                if (column.exceptions.breakdowns) {
                    result =
                        result &&
                        zemUtils.intersects(
                            column.exceptions.breakdowns,
                            breakdowns
                        );
                }

                if (column.exceptions.breakdownBaseLevelOnly) {
                    result =
                        result &&
                        column.exceptions.breakdowns.indexOf(breakdowns[0]) >=
                            0;
                }

                if (column.exceptions.levels) {
                    result =
                        result && column.exceptions.levels.indexOf(level) >= 0;
                }

                column.exceptions.custom.forEach(function(customException) {
                    if (
                        level === customException.level &&
                        breakdowns[0] === customException.breakdown
                    ) {
                        result = customException.shown;
                    }
                });
                return result;
            });
        }

        function createColumns(level, breakdowns) {
            // Create columns definitions array based on base level and breakdown
            var columns = angular.copy(getColumns(level, breakdowns));
            addRefundColumns(columns);
            adjustOrder(columns, breakdowns);
            checkPermissions(columns, breakdowns[0]);
            brandColumns(columns, breakdowns[0]);
            return columns;
        }

        function addRefundColumns(columns) {
            for (var i = columns.length - 1; i >= 0; i--) {
                var column = columns[i];
                if (column.supportsRefunds) {
                    var refundColumn = {
                        name: column.name + ' Refund',
                        field: column.field + '_refund',
                        type: column.type,
                        totalRow: column.totalRow,
                        order: false,
                        internal: false,
                        shown: false,
                        costMode: column.costMode,
                        isRefund: true,
                    };
                    columns.splice(i + 1, 0, refundColumn);
                }
            }
        }

        function createCategories() {
            return CATEGORIES.map(function(category) {
                var fields = [];
                category.columns.forEach(function(column) {
                    fields.push(column.field);
                    if (column.supportsRefunds)
                        fields.push(column.field + '_refund');
                });
                var ret = {
                    name: category.name,
                    fields: fields,
                    isNewFeature: category.isNewFeature,
                };

                if (category.description)
                    ret.description = category.description;
                return ret;
            });
        }

        function insertIntoColumns(columns, newColumns, placeholder) {
            var columnPosition = findColumnPosition(columns, placeholder);
            if (!columnPosition || arrayHelpers.isEmpty(newColumns)) return;

            var allowedColumns = newColumns.filter(function(column) {
                return (
                    column.shown &&
                    !columns.some(function(element) {
                        return element.field === column.field;
                    })
                );
            });
            Array.prototype.splice.apply(
                columns,
                [columnPosition, 0].concat(allowedColumns)
            );
        }

        function insertIntoCategories(categories, newFields, placeholder) {
            var categoryPosition = findCategoryPosition(
                categories,
                placeholder
            );
            if (!categoryPosition) return;

            Array.prototype.splice.apply(
                categoryPosition.fields,
                [categoryPosition.position, 0].concat(newFields)
            );
        }

        function setPrimaryCampaignGoal(columns, campaignGoals) {
            if (!campaignGoals) return;

            campaignGoals.forEach(function(goal) {
                angular.forEach(goal.fields, function(shown, field) {
                    if (!shown) return;
                    if (!goal.primary) return;
                    columns.forEach(function(column) {
                        if (field !== column.field) return;
                        column.default = true;
                    });
                });
            });
        }

        function setPixelColumns(columns, categories, pixels) {
            var category = findCategoryByName(categories, CategoryName.PIXELS);
            if (!category) return;

            var newColumns = [];
            category.subcategories = [];
            angular.forEach(pixels, function(pixel) {
                var pixelSubcategory = {
                    name: pixel.name,
                    prefix: pixel.prefix,
                    fields: [],
                    subcategories: [],
                };
                addPixelColumns(
                    pixelSubcategory,
                    newColumns,
                    options.conversionWindows,
                    '',
                    ' - Click attr.',
                    'Click attribution'
                );
                addPixelColumns(
                    pixelSubcategory,
                    newColumns,
                    options.conversionWindowsViewthrough,
                    '_view',
                    ' - View attr.',
                    'View attribution'
                );
                category.subcategories.push(pixelSubcategory);
            });
            checkPermissions(newColumns);
            insertIntoColumns(columns, newColumns, PIXELS_PLACEHOLDER);
        }

        function addPixelColumns(
            pixel,
            newColumns,
            conversionWindows,
            attributionSuffix,
            columnSuffix,
            attribution
        ) {
            var conversionsHelp = '';
            var conversionRateHelp = '';
            var cpaHelp = '';
            var roasHelp =
                'Return on ad spend (ROAS) is calculated by dividing revenue with advertising cost (ROAS = revenue / agency spend).\n' +
                'Your revenue is reported via value parameter on the conversion callback. You can read more about the ROAS in our help pages.';
            if (attribution === 'Click attribution') {
                conversionsHelp =
                    'The number of conversions attributed to your campaign based on user clicks.';
                conversionRateHelp =
                    'Conversion rate measures the % conversions per user click. Only conversions attributed to your campaign based on user click are counted. Calculated as 100 * Conversions / Click.';
                cpaHelp =
                    'Average cost per acquisition calculated from conversions based on user clicks.';
            }
            if (attribution === 'View attribution') {
                conversionsHelp =
                    'The number of conversions attributed to your campaign based on user viewing your ads.\n' +
                    "Conversions are based on viewable impressions. If the media source doesn't support viewable impressions the conversions are based on standard impressions.\n" +
                    "Conversions in this column don't include conversions that were attributed to a user's click.";
                conversionRateHelp =
                    'Conversion rate measures the % conversions per impression. Only conversions attributed to your campaign based on impression are counted. Calculated as 100 * Conversions / Impressions.';
                cpaHelp =
                    'Average cost per acquisition calculated from conversions based on user viewing your ads.';
            }
            angular.forEach(conversionWindows, function(window) {
                var pixelSuffix =
                    pixel.prefix + '_' + window.value + attributionSuffix;

                var conversionsField = pixelSuffix;
                var conversionRateField = CONVERSION_RATE_PREFIX + pixelSuffix;
                var etfmCpaField = AVG_ETFM_COST_PREFIX + pixelSuffix;
                var etfmRoasField = ETFM_ROAS_PREFIX + pixelSuffix;

                pixel.fields.push(
                    conversionsField,
                    conversionRateField,
                    etfmCpaField,
                    etfmRoasField
                );

                var name = pixel.name + ' ' + window.name + columnSuffix;

                var newColumn = {
                    window: window.value,
                    attribution: attribution,
                    pixel: pixel.prefix,
                };

                var conversionsNewColumn = Object.assign(
                    {},
                    COLUMNS.conversionCount,
                    newColumn,
                    {
                        restApiName: name,
                        name:
                            'Conversions / ' +
                            attribution +
                            ' (' +
                            pixel.name +
                            ')',
                        help: conversionsHelp,
                        performance: 'Conversions',
                        field: conversionsField,
                        shown: true,
                        goal: false,
                    }
                );
                var conversionRateNewColumn = Object.assign(
                    {},
                    COLUMNS.conversionRate,
                    newColumn,
                    {
                        restApiName: 'Conversion rate (' + name + ')',
                        name:
                            'Conversion rate / ' +
                            attribution +
                            ' (' +
                            pixel.name +
                            ')',
                        help: conversionRateHelp,
                        performance: 'Conversion rate',
                        field: conversionRateField,
                        shown: true,
                        goal: false,
                    }
                );
                var etfmCpaNewColumn = Object.assign(
                    {},
                    COLUMNS.conversionCpa,
                    newColumn,
                    {
                        restApiName: 'CPA (' + name + ')',
                        name: 'CPA / ' + attribution + ' (' + pixel.name + ')',
                        help: cpaHelp,
                        performance: 'CPA',
                        field: etfmCpaField,
                        shown: true,
                        goal: true,
                        costMode: constants.costMode.PUBLIC,
                    }
                );
                var etfmRoasNewColumn = Object.assign(
                    {},
                    COLUMNS.conversionRoas,
                    newColumn,
                    {
                        restApiName: 'ROAS (' + name + ')',
                        name: 'ROAS / ' + attribution + ' (' + pixel.name + ')',
                        performance: 'ROAS',
                        field: etfmRoasField,
                        shown: true,
                        costMode: constants.costMode.PUBLIC,
                        help: roasHelp,
                    }
                );

                newColumns.push(
                    conversionsNewColumn,
                    conversionRateNewColumn,
                    etfmCpaNewColumn,
                    etfmRoasNewColumn
                );
            });
        }

        function setConversionGoalColumns(
            columns,
            categories,
            conversionGoals
        ) {
            if (!conversionGoals) return;

            var orderedColumns = [],
                newFields = [];
            angular.forEach(conversionGoals, function(goal) {
                var conversionsCol = angular.copy(COLUMNS.conversionCount);
                conversionsCol.name = goal.name;
                conversionsCol.field = goal.id;
                conversionsCol.shown = true;

                var etfmCpaCol = angular.copy(COLUMNS.conversionCpa);
                etfmCpaCol.name = 'CPA (' + goal.name + ')';
                etfmCpaCol.field = AVG_ETFM_COST_PREFIX + goal.id;
                etfmCpaCol.shown = true;
                etfmCpaCol.goal = true;
                etfmCpaCol.costMode = constants.costMode.PUBLIC;
                etfmCpaCol.shown = true;

                newFields.push(conversionsCol.field);
                newFields.push(etfmCpaCol.field);

                orderedColumns.push(conversionsCol);
                orderedColumns.push(etfmCpaCol);
            });

            checkPermissions(orderedColumns);
            insertIntoColumns(
                columns,
                orderedColumns,
                CONVERSION_GOALS_PLACEHOLDER
            );
            insertIntoCategories(
                categories,
                newFields,
                CONVERSION_GOALS_PLACEHOLDER
            );
        }

        function setDynamicColumns(
            columns,
            categories,
            campaignGoals,
            conversionGoals,
            pixels
        ) {
            setPixelColumns(columns, categories, pixels);
            setConversionGoalColumns(columns, categories, conversionGoals);
            setPrimaryCampaignGoal(columns, campaignGoals);
        }

        function findCategoryByName(categories, name) {
            for (var i = 0; i < categories.length; i++) {
                if (categories[i].name === name) {
                    return categories[i];
                }
            }
        }

        function findColumnPosition(columns, field) {
            for (var i = 0; i < columns.length; i++) {
                if (columns[i].field === field) {
                    // return next index
                    return i + 1;
                }
            }
        }

        function findCategoryPosition(categories, field) {
            for (var i = 0; i < categories.length; i++) {
                for (var j = 0; j < categories[i].fields.length; j++) {
                    if (categories[i].fields[j] === field) {
                        return {
                            fields: categories[i].fields,
                            position: j + 1, // return next index
                        };
                    }
                }
            }
        }

        function findColumnByField(field) {
            if (!findColumnByField.cache) {
                findColumnByField.cache = {};
                angular.forEach(COLUMNS, function(column) {
                    findColumnByField.cache[column.field] = column;
                });
            }
            return findColumnByField.cache[field];
        }

        var AUDIENCE_METRICS_FIELDS = AUDIENCE_METRICS_GROUP.map(function(
            column
        ) {
            return column.field;
        });
        function isAudienceMetricColumn(column) {
            if (!column) {
                return false;
            }
            return AUDIENCE_METRICS_FIELDS.indexOf(column.field) !== -1;
        }

        return {
            COLUMNS: COLUMNS,
            findColumnByField: findColumnByField,
            isAudienceMetricColumn: isAudienceMetricColumn,
            createColumns: createColumns,
            createCategories: createCategories,
            setDynamicColumns: setDynamicColumns,
        };
    });
