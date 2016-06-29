/* globals oneApp, angular, constants */
'use strict';

oneApp.factory('zemGridEndpointColumns', ['zemGridConstants', function (zemGridConstants) {
    var CONVERSION_GOAL_FIELD_PREFIX = 'conversion_goal_';
    var AVG_COST_PER_CONVERSION_GOAL_PREFIX = 'avg_cost_per_conversion_goal_';

    // //////////////////////////////////////////////////////////////////////////////////////////////////
    // BASE COLUMNS DEFINITIONS
    //
    var COLUMNS = {
        account: {
            name: 'Account',
            field: 'breakdown_name',
            unselectable: true,
            checked: true,
            type: zemGridConstants.gridColumnTypes.BREAKDOWN,
            shown: true,
            totalRow: false,
            help: 'A partner account.',
            order: true,
            orderField: 'name',
            initialOrder: zemGridConstants.gridColumnOrder.ASC,
        },
        campaign: {
            name: 'Campaign',
            field: 'breakdown_name',
            unselectable: true,
            checked: true,
            type: zemGridConstants.gridColumnTypes.BREAKDOWN,
            shown: true,
            totalRow: false,
            help: 'Name of the campaign.',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.ASC,
        },
        adgroup: {
            name: 'Ad Group',
            field: 'breakdown_name',
            unselectable: true,
            checked: true,
            type: zemGridConstants.gridColumnTypes.BREAKDOWN,
            shown: true,
            totalRow: false,
            help: 'Name of the ad group.',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.ASC,
        },
        mediaSource: {
            name: 'Media Source',
            field: 'breakdown_name',
            unselectable: true,
            checked: true,
            type: zemGridConstants.gridColumnTypes.BREAKDOWN,
            totalRow: false,
            help: 'A media source where your content is being promoted.',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.ASC,
            hasPermission: 'zemauth.can_filter_sources_through_table',
            shown: true,
        },

        agency: {
            name: 'Agency',
            field: 'agency',
            unselectable: true,
            checked: true,
            type: zemGridConstants.gridColumnTypes.TEXT,
            totalRow: false,
            help: 'Agency to which this account belongs.',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_view_account_agency_information',
            shown: 'zemauth.can_view_account_agency_information',
        },
        defaultAccountManager: {
            name: 'Account Manager',
            field: 'default_account_manager',
            checked: false,
            type: zemGridConstants.gridColumnTypes.TEXT,
            totalRow: false,
            help: 'Account manager responsible for the campaign and the communication with the client.',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_see_managers_in_accounts_table',
            shown: 'zemauth.can_see_managers_in_accounts_table',
        },
        defaultSalesRepresentative: {
            name: 'Sales Representative',
            field: 'default_sales_representative',
            checked: false,
            type: zemGridConstants.gridColumnTypes.TEXT,
            totalRow: false,
            help: 'Sales representative responsible for the campaign and the communication with the client.',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_see_managers_in_accounts_table',
            shown: 'zemauth.can_see_managers_in_accounts_table',
        },
        campaignManager: {
            name: 'Campaign Manager',
            field: 'campaign_manager',
            checked: false,
            type: zemGridConstants.gridColumnTypes.TEXT,
            totalRow: false,
            help: 'Campaign manager responsible for the campaign and the communication with the client.',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_see_managers_in_campaigns_table',
            shown: 'zemauth.can_see_managers_in_campaigns_table',
        },
        accountType: {
            name: 'Account Type',
            field: 'account_type',
            checked: false,
            type: zemGridConstants.gridColumnTypes.TEXT,
            totalRow: false,
            help: 'Type of account.',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_see_account_type',
            shown: 'zemauth.can_see_account_type',
        },
        performance: {
            nameCssClass: 'performance-icon',
            field: 'performance',
            unselectable: true,
            checked: true,
            type: zemGridConstants.gridColumnTypes.PERFORMANCE_INDICATOR,
            totalRow: false,
            help: 'Goal performance indicator',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.ASC,
            internal: 'zemauth.campaign_goal_performance',
            shown: 'zemauth.campaign_goal_performance',
        },

        // State
        stateAdGroup: { // AdGroup state
            name: '\u25CF',
            field: 'state',
            type: zemGridConstants.gridColumnTypes.STATE_SELECTOR,
            order: true,
            editable: true,
            initialOrder: zemGridConstants.gridColumnOrder.ASC,
            checked: true,
            totalRow: false,
            unselectable: true,
            help: 'A setting for enabling and pausing Ad Groups.',
            disabled: false,
            internal: 'zemauth.can_control_ad_group_state_in_table',
            shown: 'zemauth.can_control_ad_group_state_in_table',
        },
        stateContentAd: {
            name: '\u25CF',
            field: 'status_setting',
            type: zemGridConstants.gridColumnTypes.STATE_SELECTOR,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.ASC,
            internal: false,
            shown: true,
            checked: true,
            totalRow: false,
            unselectable: true,
            help: 'A setting for enabling and pausing content ads.',
            disabled: false,
            archivedField: 'archived',
        },

        // Status columns
        statusAccount: {
            name: 'Status',
            field: 'status',
            unselectable: true,
            checked: true,
            type: zemGridConstants.gridColumnTypes.STATUS,
            shown: true,
            totalRow: false,
            help: 'Status of an account (enabled or paused). An account is paused only if all its campaigns ' +
            'are paused too; otherwise the account is enabled.',
            order: true,
            orderField: 'status',
            initialOrder: zemGridConstants.gridColumnOrder.ASC,
        },
        statusCampaign: {
            name: 'Status',
            field: 'state',
            checked: true,
            type: zemGridConstants.gridColumnTypes.STATUS,
            shown: true,
            totalRow: false,
            help: 'Status of a campaign (enabled or paused). A campaign is paused only if all its ad groups ' +
            'are paused too; otherwise, the campaign is enabled.',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.ASC,
        },
        statusAdGroup: {
            name: 'Status',
            field: 'stateText',
            unselectable: true,
            checked: true,
            type: zemGridConstants.gridColumnTypes.STATUS,
            shown: true,
            totalRow: false,
            help: 'Status of an ad group (enabled or paused).',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.ASC,
        },
        statusContentAd: {
            name: 'Status',
            field: 'submission_status',
            checked: false,
            type: zemGridConstants.gridColumnTypes.SUBMISSION_STATUS,
            archivedField: 'archived',
            shown: true,
            help: 'Current submission status.',
            totalRow: false,
        },
        statusMediaSource: {
            name: 'Status',
            field: 'status',
            unselectable: true,
            checked: true,
            type: zemGridConstants.gridColumnTypes.STATUS,
            shown: true,
            totalRow: false,
            help: 'Status of a particular media source (enabled or paused).',
            order: true,
            orderField: 'status',
            initialOrder: zemGridConstants.gridColumnOrder.ASC,
        },
        statusMediaSourceAdGroup: {
            name: 'Status',
            field: 'status',
            unselectable: true,
            checked: true,
            type: zemGridConstants.gridColumnTypes.NOTIFICATION,
            shown: true,
            totalRow: false,
            help: 'Status of a particular media source (enabled or paused).',
            order: true,
            orderField: 'status',
            initialOrder: zemGridConstants.gridColumnOrder.ASC,
        },
        statusPublisher: {
            name: 'Status',
            field: 'blacklisted',
            checked: true,
            type: zemGridConstants.gridColumnTypes.TEXT_WITH_POPUP,
            popupField: 'blacklisted_level_description',
            help: 'Blacklisted status of a publisher.',
            totalRow: false,
            order: false,
            initialOrder: zemGridConstants.gridColumnOrder.ASC,
            shown: 'zemauth.can_see_publisher_blacklist_status',
        },

        // Media source
        minBidCpc: {
            name: 'Min Bid',
            field: 'min_bid_cpc',
            checked: true,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            shown: true,
            fractionSize: 3,
            help: 'Minimum bid price (in USD) per click.',
            totalRow: false,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
        maxBidCpc: {
            name: 'Max Bid',
            field: 'max_bid_cpc',
            checked: true,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            shown: true,
            fractionSize: 3,
            help: 'Maximum bid price (in USD) per click.',
            totalRow: false,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
        dailyBudget: {
            name: 'Daily Budget',
            field: 'daily_budget',
            checked: true,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            shown: true,
            help: 'Maximum budget per day.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
        supplyDashUrl: {
            name: 'Link',
            field: 'supply_dash_url',
            checked: false,
            type: 'link',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.supply_dash_link_view',
            shown: 'zemauth.supply_dash_link_view',
        },

        // AdGroup Media Sources
        bidCpcSetting: {
            name: 'Bid CPC',
            field: 'bid_cpc',
            checked: true,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            shown: true,
            fractionSize: 3,
            help: 'Maximum bid price (in USD) per click.',
            totalRow: false,
            order: true,
            settingsField: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
        currentBidCpc: {
            name: 'Current Bid CPC',
            field: 'current_bid_cpc',
            fractionSize: 3,
            checked: false,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            internal: false,
            shown: false,
            totalRow: false,
            order: true,
            help: 'Cost-per-click (CPC) bid is the approximate amount that you\'ll be charged for a click on your ad.',
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
        dailyBudgetSetting: {
            name: 'Daily Budget',
            field: 'daily_budget',
            fractionSize: 0,
            checked: true,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            shown: true,
            help: 'Maximum budget per day.',
            totalRow: true,
            order: true,
            settingsField: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
        currentDailyBudget: {
            name: 'Current Daily Budget',
            field: 'current_daily_budget',
            checked: false,
            fractionSize: 0,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            internal: false,
            shown: false,
            totalRow: true,
            order: true,
            help: 'Maximum budget per day.',
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },

        // Content Ad
        imageUrls: {
            name: 'Thumbnail',
            field: 'image_urls',
            checked: true,
            type: zemGridConstants.gridColumnTypes.THUMBNAIL,
            shown: true,
            totalRow: false,
            titleField: 'title',
            order: true,
            orderField: 'image_hash',
            initialOrder: zemGridConstants.gridColumnOrder.ASC,
        },
        notification: {
            name: '',
            unselectable: true,
            checked: true,
            type: zemGridConstants.gridColumnTypes.NOTIFICATION,
            shown: true,
            totalRow: false,
        },
        titleLink: {
            name: 'Title',
            field: 'titleLink',
            checked: true,
            type: 'linkText',
            shown: true,
            totalRow: false,
            help: 'The creative title/headline of a content ad. The link to landing page includes tracking codes.',
            titleField: 'title',
            order: true,
            orderField: 'title',
            initialOrder: zemGridConstants.gridColumnOrder.ASC,
        },
        urlLink: {
            name: 'URL',
            field: 'urlLink',
            checked: true,
            type: 'linkText',
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
            checked: true,
            type: zemGridConstants.gridColumnTypes.DATE_TIME,
            shown: true,
            help: 'The time when the content ad was uploaded.',
            totalRow: false,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
        batchName: {
            name: 'Batch Name',
            field: 'batch_name',
            checked: true,
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
            checked: false,
            type: zemGridConstants.gridColumnTypes.TEXT,
            shown: true,
            help: 'Advertiser\'s display URL.',
            totalRow: false,
            titleField: 'display_url',
            order: true,
            orderField: 'display_url',
            initialOrder: zemGridConstants.gridColumnOrder.ASC,
        },
        brandName: {
            name: 'Brand Name',
            field: 'brand_name',
            checked: false,
            type: zemGridConstants.gridColumnTypes.TEXT,
            shown: true,
            help: 'Advertiser\'s brand name',
            totalRow: false,
            titleField: 'brand_name',
            order: true,
            orderField: 'brand_name',
            initialOrder: zemGridConstants.gridColumnOrder.ASC,
        },
        description: {
            name: 'Description',
            field: 'description',
            checked: false,
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
            checked: false,
            type: zemGridConstants.gridColumnTypes.TEXT,
            shown: true,
            help: 'Call to action text.',
            totalRow: false,
            titleField: 'call_to_action',
            order: true,
            orderField: 'call_to_action',
            initialOrder: zemGridConstants.gridColumnOrder.ASC,
        },

        // Publisher
        domain: {
            name: 'Domain',
            field: 'domain',
            unselectable: false,
            checked: true,
            type: 'clickPermissionOrText',
            shown: true,
            totalRow: false,
            help: 'A publisher where your content is being promoted.',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.ASC,
        },
        domainLink: {
            name: 'Link',
            field: 'domain_link',
            unselectable: false,
            checked: true,
            type: 'visibleLink',
            shown: true,
            totalRow: false,
            help: 'Link to a publisher where your content is being promoted.',
            order: false,
            initialOrder: zemGridConstants.gridColumnOrder.ASC,
        },
        exchange: {
            name: 'Media Source',
            field: 'exchange',
            unselectable: false,
            checked: true,
            type: 'clickPermissionOrText',
            shown: true,
            totalRow: false,
            help: 'An exchange where your content is being promoted.',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.ASC,
        },

        // Costs
        mediaCost: {
            name: 'Actual Media Spend',
            field: 'media_cost',
            checked: false,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            totalRow: true,
            help: 'Amount spent per media source, including overspend.',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_view_actual_costs',
            shown: 'zemauth.can_view_actual_costs',
        },
        eMediaCost: {
            name: 'Media Spend',
            field: 'e_media_cost',
            checked: false,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            totalRow: true,
            help: 'Amount spent per media source.',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_view_effective_costs',
            shown: 'zemauth.can_view_effective_costs',
        },
        dataCost: {
            name: 'Actual Data Cost',
            field: 'data_cost',
            checked: false,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            totalRow: true,
            help: 'Additional targeting/segmenting costs, including overspend.',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_view_actual_costs',
            shown: 'zemauth.can_view_actual_costs',
        },
        eDataCost: {
            name: 'Data Cost',
            field: 'e_data_cost',
            checked: false,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            totalRow: true,
            help: 'Additional targeting/segmenting costs.',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_view_effective_costs',
            shown: 'zemauth.can_view_effective_costs',
        },
        licenseFee: {
            name: 'License Fee',
            field: 'license_fee',
            checked: false,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            totalRow: true,
            help: 'Zemanta One platform usage cost.',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_view_effective_costs',
            shown: 'zemauth.can_view_effective_costs',
        },
        flatFee: {
            name: 'Recognized Flat Fee',
            field: 'flat_fee',
            checked: false,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            totalRow: true,
            help: '',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_view_flat_fees',
            shown: 'zemauth.can_view_flat_fees',
        },
        totalFee: {
            name: 'Total Fee',
            field: 'total_fee',
            checked: false,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            totalRow: true,
            help: '',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_view_flat_fees',
            shown: 'zemauth.can_view_flat_fees',
        },
        billingCost: {
            name: 'Total Spend',
            field: 'billing_cost',
            checked: false,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            totalRow: true,
            help: 'Sum of media spend, data cost and license fee.',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_view_effective_costs',
            shown: 'zemauth.can_view_effective_costs',
        },
        cpc: {
            name: 'Avg. CPC',
            field: 'cpc',
            checked: true,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            shown: true,
            fractionSize: 3,
            help: 'The average CPC.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },

        // Yesterday cost metrics
        yesterdayCost: {
            name: 'Actual Yesterday Spend',
            field: 'yesterday_cost',
            checked: false,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            help: 'Amount that you have spent yesterday for promotion on specific ad group, including overspend.',
            totalRow: true,
            order: true,
            internal: 'zemauth.can_view_actual_costs',
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            shown: 'zemauth.can_view_actual_costs',
        },
        eYesterdayCost: {
            name: 'Yesterday Spend',
            field: 'e_yesterday_cost',
            checked: false,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            help: 'Amount that you have spent yesterday for promotion on specific ad group.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_view_effective_costs',
            shown: 'zemauth.can_view_effective_costs',
        },

        // Traffic metrics
        clicks: {
            name: 'Clicks',
            field: 'clicks',
            checked: true,
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
            checked: true,
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
            checked: true,
            type: zemGridConstants.gridColumnTypes.PERCENT,
            shown: true,
            defaultValue: '0.0%',
            totalRow: true,
            help: 'The number of clicks divided by the number of impressions.',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },

        // Projection metrics
        allocatedBudgets: {
            name: 'Media budgets',
            field: 'allocated_budgets',
            checked: false,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            totalRow: true,
            help: '',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_see_projections',
            shown: 'zemauth.can_see_projections',
        },
        pacing: {
            name: 'Pacing',
            field: 'pacing',
            checked: false,
            type: zemGridConstants.gridColumnTypes.PERCENT,
            totalRow: true,
            help: '',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_see_projections',
            shown: 'zemauth.can_see_projections',
        },
        spendProjection: {
            name: 'Spend Projection',
            field: 'spend_projection',
            checked: false,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            totalRow: true,
            help: '',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_see_projections',
            shown: 'zemauth.can_see_projections',
        },
        licenseFeeProjection: {
            name: 'License Fee Projection',
            field: 'license_fee_projection',
            checked: false,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            totalRow: true,
            help: '',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_see_projections',
            shown: 'zemauth.can_see_projections',
        },
        totalFeeProjection: {
            name: 'Total Fee Projection',
            field: 'total_fee_projection',
            checked: false,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            totalRow: true,
            help: '',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_see_projections',
            shown: ['zemauth.can_see_projections', 'zemauth.can_view_flat_fees'],
        },

        // Optimisation metrics
        totalSeconds: {
            name: 'Total Seconds',
            field: 'total_seconds',
            checked: true,
            type: zemGridConstants.gridColumnTypes.NUMBER,
            shown: false,
            internal: 'zemauth.campaign_goal_optimization',
            help: 'Total time spend on site.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
        unbouncedVisits: {
            name: 'Unbounced Visitors',
            field: 'unbounced_visits',
            checked: false,
            type: zemGridConstants.gridColumnTypes.NUMBER,
            shown: false,
            internal: 'zemauth.campaign_goal_optimization',
            help: 'Percent of visitors that navigate to more than one page on the site.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
        totalPageviews: {
            name: 'Total Pageviews',
            field: 'total_pageviews',
            checked: true,
            type: zemGridConstants.gridColumnTypes.NUMBER,
            shown: false,
            internal: 'zemauth.campaign_goal_optimization',
            help: 'Total pageviews.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
        avgCostPerSecond: {
            name: 'Avg. Cost per Minute',
            field: 'avg_cost_per_minute',
            checked: true,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            shown: false,
            internal: 'zemauth.campaign_goal_optimization',
            help: 'Average cost per minute spent on site.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
        avgCostPerPageview: {
            name: 'Avg. Cost per Pageview',
            field: 'avg_cost_per_pageview',
            checked: true,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            shown: false,
            internal: 'zemauth.campaign_goal_optimization',
            help: 'Average cost per pageview.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
        avgCostPerVisit: {
            name: 'Avg. Cost per Visit',
            field: 'avg_cost_per_visit',
            checked: true,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            shown: false,
            internal: 'zemauth.campaign_goal_optimization',
            help: 'Average cost per visit.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
        avgCostPerNonBouncedVisitor: {
            name: 'Avg. Cost for Unbounced Visitor',
            field: 'avg_cost_per_non_bounced_visitor',
            checked: true,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            shown: false,
            internal: 'zemauth.campaign_goal_optimization',
            help: 'Average cost per non-bounced visitors.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
        avgCostForNewVisitor: {
            name: 'Avg. Cost for New Visitor',
            field: 'avg_cost_for_new_visitor',
            checked: true,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            shown: false,
            internal: 'zemauth.campaign_goal_optimization',
            help: 'Average cost for new visitor.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },

        // Postclick Engagement Metrics
        percentNewUsers: {
            name: '% New Users',
            field: 'percent_new_users',
            checked: false,
            type: zemGridConstants.gridColumnTypes.PERCENT,
            shown: 'zemauth.aggregate_postclick_engagement',
            internal: 'zemauth.aggregate_postclick_engagement',
            help: 'An estimate of first time visits during the selected date range.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
        bounceRate: {
            name: 'Bounce Rate',
            field: 'bounce_rate',
            checked: false,
            type: zemGridConstants.gridColumnTypes.PERCENT,
            shown: 'zemauth.aggregate_postclick_engagement',
            internal: 'zemauth.aggregate_postclick_engagement',
            help: 'Percentage of visits that resulted in only one page view.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
        pvPerVisit: {
            name: 'Pageviews per Visit',
            field: 'pv_per_visit',
            checked: false,
            type: zemGridConstants.gridColumnTypes.NUMBER,
            fractionSize: 2,
            shown: 'zemauth.aggregate_postclick_engagement',
            internal: 'zemauth.aggregate_postclick_engagement',
            help: 'Average number of pageviews per visit.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
        avgTos: {
            name: 'Time on Site',
            field: 'avg_tos',
            checked: false,
            type: zemGridConstants.gridColumnTypes.SECONDS,
            shown: 'zemauth.aggregate_postclick_engagement',
            internal: 'zemauth.aggregate_postclick_engagement',
            help: 'Average time spent on site in seconds during the selected date range.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },

        // Postclick acquisition metrics
        visits: {
            name: 'Visits',
            field: 'visits',
            checked: true,
            type: zemGridConstants.gridColumnTypes.NUMBER,
            shown: 'zemauth.aggregate_postclick_acquisition',
            internal: 'zemauth.aggregate_postclick_acquisition',
            help: 'Total number of sessions within a date range. A session is the period of time in which a user ' +
            'is actively engaged with your site.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
        clickDiscrepancy: {
            name: 'Click Discrepancy',
            field: 'click_discrepancy',
            checked: false,
            type: zemGridConstants.gridColumnTypes.PERCENT,
            shown: 'zemauth.aggregate_postclick_acquisition',
            internal: 'zemauth.aggregate_postclick_acquisition',
            help: 'Clicks detected only by media source as a percentage of total clicks.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
        pageviews: {
            name: 'Pageviews',
            field: 'pageviews',
            checked: true,
            type: zemGridConstants.gridColumnTypes.NUMBER,
            shown: 'zemauth.aggregate_postclick_acquisition',
            internal: 'zemauth.aggregate_postclick_acquisition',
            help: 'Total number of pageviews made during the selected date range. A pageview is a view of ' +
            'a single page. Repeated views are counted.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
    };

    for (var i = 1; i <= 5; i++) {
        COLUMNS['conversionGoal' + i] = {
            name: 'Conversion Goal ' + i,
            field: CONVERSION_GOAL_FIELD_PREFIX + i,
            checked: false,
            type: zemGridConstants.gridColumnTypes.NUMBER,
            help: 'Number of completions of the conversion goal',
            shown: false,
            internal: false,
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        };
    }

    for (i = 0; i < 6; i++) {
        COLUMNS['avgCostPerConversionGoal' + i] = {
            name: 'Avg. CPA',
            field: AVG_COST_PER_CONVERSION_GOAL_PREFIX + i,
            checked: false,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            shown: false,
            internal: 'zemauth.campaign_goal_optimization',
            help: 'Average cost per acquisition.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        };
    }

    var BASE_METRICS = [
        COLUMNS.licenseFee,
        COLUMNS.mediaCost,
        COLUMNS.eMediaCost,
        COLUMNS.dataCost,
        COLUMNS.eDataCost,
        COLUMNS.billingCost,
        COLUMNS.cpc,
        COLUMNS.clicks,
        COLUMNS.impressions,
        COLUMNS.ctr,
    ];

    var OPTIMISATION_METRICS = [
        COLUMNS.totalSeconds,
        COLUMNS.unbouncedVisits,
        COLUMNS.totalPageviews,
        COLUMNS.avgCostPerSecond,
        COLUMNS.avgCostPerPageview,
        COLUMNS.avgCostPerNonBouncedVisitor,
        COLUMNS.avgCostPerConversionGoal0,
        COLUMNS.avgCostPerConversionGoal1,
        COLUMNS.avgCostPerConversionGoal2,
        COLUMNS.avgCostPerConversionGoal3,
        COLUMNS.avgCostPerConversionGoal4,
        COLUMNS.avgCostPerConversionGoal5,
        COLUMNS.avgCostForNewVisitor,
    ];

    var POSTCLICK_ENGAGEMENT_METRICS = [
        COLUMNS.percentNewUsers,
        COLUMNS.bounceRate,
        COLUMNS.pvPerVisit,
        COLUMNS.avgTos,
    ];

    var POSTCLICK_ACQUISITION_METRICS = [
        COLUMNS.visits,
        COLUMNS.clickDiscrepancy,
        COLUMNS.pageviews,
    ];

    var POSTCLICK_CONVERSION_GOALS_METRICS = [
        COLUMNS.conversionGoal1,
        COLUMNS.conversionGoal2,
        COLUMNS.conversionGoal3,
        COLUMNS.conversionGoal4,
        COLUMNS.conversionGoal5,
    ];

    var ALL_ACCOUNTS_ACCOUNTS = [
        COLUMNS.account,
        COLUMNS.agency,
        COLUMNS.statusAccount,
        COLUMNS.defaultAccountManager,
        COLUMNS.defaultSalesRepresentative,
        COLUMNS.accountType,
        COLUMNS.allocatedBudgets,
        COLUMNS.spendProjection,
        COLUMNS.pacing,
        COLUMNS.flatFee,
        COLUMNS.totalFee,
        COLUMNS.totalFeeProjection,
        COLUMNS.licenseFeeProjection,
    ].concat(
        BASE_METRICS,
        POSTCLICK_ACQUISITION_METRICS,
        POSTCLICK_ENGAGEMENT_METRICS
    );

    var ACCOUNT_CAMPAIGNS = [
        COLUMNS.campaign,
        COLUMNS.performance,
        COLUMNS.statusCampaign,
        COLUMNS.campaignManager,
        COLUMNS.allocatedBudgets,
        COLUMNS.spendProjection,
        COLUMNS.pacing,
        COLUMNS.licenseFeeProjection,
    ].concat(
        BASE_METRICS,
        POSTCLICK_ACQUISITION_METRICS,
        POSTCLICK_ENGAGEMENT_METRICS
    );

    var CAMPAIGN_AD_GROUPS = [
        COLUMNS.stateAdGroup,
        COLUMNS.adgroup,
        COLUMNS.performance,
        COLUMNS.statusAdGroup,
        COLUMNS.yesterdayCost,
        COLUMNS.eYesterdayCost,
    ].concat(
        BASE_METRICS,
        POSTCLICK_ACQUISITION_METRICS,
        POSTCLICK_ENGAGEMENT_METRICS,
        POSTCLICK_CONVERSION_GOALS_METRICS,
        OPTIMISATION_METRICS
    );

    var AD_GROUP_CONTENT_ADS = [
        COLUMNS.imageUrls,
        COLUMNS.stateContentAd,
        COLUMNS.performance,
        COLUMNS.statusContentAd,
        COLUMNS.notification,
        COLUMNS.titleLink,
        COLUMNS.urlLink,
        COLUMNS.uploadTime,
        COLUMNS.batchName,
        COLUMNS.displayUrl,
        COLUMNS.brandName,
        COLUMNS.description,
        COLUMNS.callToAction,
    ].concat(
        BASE_METRICS,
        POSTCLICK_ACQUISITION_METRICS,
        POSTCLICK_ENGAGEMENT_METRICS,
        POSTCLICK_CONVERSION_GOALS_METRICS,
        OPTIMISATION_METRICS
    );

    var MEDIA_SOURCE = [
        COLUMNS.mediaSource,
        COLUMNS.performance,
        COLUMNS.statusMediaSource,
        COLUMNS.minBidCpc,
        COLUMNS.maxBidCpc,
        COLUMNS.dailyBudget,
        COLUMNS.yesterdayCost,
        COLUMNS.eYesterdayCost,
    ].concat(
        BASE_METRICS,
        POSTCLICK_ACQUISITION_METRICS,
        POSTCLICK_ENGAGEMENT_METRICS
    );

    var CAMPAIGN_MEDIA_SOURCE = [].concat(
        MEDIA_SOURCE,
        POSTCLICK_CONVERSION_GOALS_METRICS,
        OPTIMISATION_METRICS
    );

    var AD_GROUP_MEDIA_SOURCE = [
        COLUMNS.mediaSource,
        COLUMNS.performance,
        COLUMNS.statusMediaSourceAdGroup,
        COLUMNS.supplyDashUrl,
        COLUMNS.bidCpcSetting,
        COLUMNS.currentBidCpc,
        COLUMNS.currentBidCpc,
        COLUMNS.dailyBudgetSetting,
        COLUMNS.currentDailyBudget,
        COLUMNS.yesterdayCost,
        COLUMNS.eYesterdayCost,
    ].concat(
        BASE_METRICS,
        POSTCLICK_ACQUISITION_METRICS,
        POSTCLICK_ENGAGEMENT_METRICS,
        POSTCLICK_CONVERSION_GOALS_METRICS,
        OPTIMISATION_METRICS
    );

    var AD_GROUP_PUBLISHERS = [
        COLUMNS.statusPublisher,
        COLUMNS.performance,
        COLUMNS.domain,
        COLUMNS.domainLink,
        COLUMNS.exchange,
    ].concat(
        BASE_METRICS,
        POSTCLICK_ACQUISITION_METRICS,
        POSTCLICK_ENGAGEMENT_METRICS,
        POSTCLICK_CONVERSION_GOALS_METRICS,
        OPTIMISATION_METRICS
    );


    // //////////////V////////////////////////////////////////////////////////////////////////////////////
    //  COLUMN CATEGORIES
    //
    var CATEGORIES = [
        {
            name: 'Costs',
            columns: [
                COLUMNS.dataCost,
                COLUMNS.mediaCost,
                COLUMNS.eMediaCost,
                COLUMNS.eDataCost,
                COLUMNS.billingCost,
                COLUMNS.licenseFee,
                COLUMNS.flatFee,
                COLUMNS.totalFee,
                COLUMNS.yesterdayCost,
                COLUMNS.eYesterdayCost,
            ],
        },
        {
            name: 'Content Sync',
            columns: [
                COLUMNS.imageUrls,
                COLUMNS.titleLink,
                COLUMNS.urlLink,
                COLUMNS.statusContentAd,
                COLUMNS.uploadTime,
                COLUMNS.batchName,
                COLUMNS.displayUrl,
                COLUMNS.brandName,
                COLUMNS.description,
                COLUMNS.callToAction,
            ],
        },
        {
            name: 'Projections',
            columns: [
                COLUMNS.pacing,
                COLUMNS.allocatedBudgets,
                COLUMNS.spendProjection,
                COLUMNS.licenseFeeProjection,
                COLUMNS.totalFeeProjection,
            ],
        },
        {
            name: 'Traffic Acquisition',
            columns: [
                COLUMNS.clicks,
                COLUMNS.impressions,
                COLUMNS.ctr,
                COLUMNS.statusPublisher,
                COLUMNS.domain,
                COLUMNS.domainLink,
                COLUMNS.exchange,
                COLUMNS.minBidCpc,
                COLUMNS.maxBidCpc,
                COLUMNS.dailyBudget,
                COLUMNS.dailyBudgetSetting,
            ],
        },
        {
            name: 'Audience Metrics',
            columns: [].concat(POSTCLICK_ACQUISITION_METRICS, POSTCLICK_ENGAGEMENT_METRICS),
        },
        {
            name: 'Management',
            columns: [
                COLUMNS.defaultAccountManager,
                COLUMNS.defaultSalesRepresentative,
                COLUMNS.campaignManager,
                COLUMNS.accountType,
            ],
        },
        {
            name: 'Conversions',
            columns: POSTCLICK_CONVERSION_GOALS_METRICS,
        },
        {
            name: 'Campaign Goals',
            columns: OPTIMISATION_METRICS,
        },
    ];

    // ///////////////////////////////////////////////////////////////////////////////////////////////////
    // Service functions
    //

    function convertPermission (permission, checkFn) {
        // Convert Column definitions permissions to boolean value using passed function
        // Possible types: boolean, string, array
        var result = false;
        if (typeof permission === 'boolean') {
            result = permission;
        } else if (typeof permission === 'string') {
            var negate = false;
            if (permission[0] === '!') {
                negate = true;
                permission = permission.substring(1);
            }
            result = checkFn(permission);
            if (negate) result = !result;
        } else if (permission instanceof Array) {
            result = true;
            permission.forEach(function (p) {
                result = result && convertPermission(p, checkFn);
            });
        }
        return result;
    }

    function checkPermissions ($scope, columns) {
        // Go trough all columns and convert permissions to boolean, when needed
        columns.forEach(function (column) {
            column.internal = convertPermission(column.internal, $scope.isPermissionInternal);
            column.shown = convertPermission(column.shown, $scope.hasPermission);
        });
    }

    function getColumns (level, breakdown) {
        // TODO: create breakdown constants
        if (breakdown === 'source') {
            switch (level) {
            case constants.level.AD_GROUPS: return AD_GROUP_MEDIA_SOURCE;
            case constants.level.CAMPAIGNS: return CAMPAIGN_MEDIA_SOURCE;
            default: return MEDIA_SOURCE;
            }
        } else if (breakdown === 'publisher') {
            switch (level) {
            case constants.level.AD_GROUPS: return AD_GROUP_PUBLISHERS;
            default: throw 'Not supported.';
            }
        } else {
            switch (level) {
            case constants.level.ALL_ACCOUNTS: return ALL_ACCOUNTS_ACCOUNTS;
            case constants.level.ACCOUNTS: return ACCOUNT_CAMPAIGNS;
            case constants.level.CAMPAIGNS: return CAMPAIGN_AD_GROUPS;
            case constants.level.AD_GROUPS: return AD_GROUP_CONTENT_ADS;
            default: throw 'Not supported.';
            }
        }
    }

    function createColumns ($scope, level, breakdown) {
        // Create columns definitions array based on base level and breakdown
        var columns = angular.copy(getColumns(level, breakdown));
        checkPermissions($scope, columns);
        return columns;
    }

    function createCategories () {
        return CATEGORIES.map(function (category) {
            var fields = category.columns.map(function (column) {
                return column.field;
            });
            return {
                name: category.name,
                fields: fields,
            };
        });
    }

    function updateConversionGoalColumns (columns, goals) {
        if (!goals) return;

        goals.forEach(function (goal) {
            columns.forEach(function (column) {
                if (column.field !== goal.id) return;
                column.shown = true;
                column.name = goal.name;
            });
        });
    }

    function updateOptimizationGoalColumns (columns, goals) {
        if (!goals) return;

        goals.forEach(function (goal) {
            angular.forEach(goal.fields, function (shown, field) {
                if (!shown) return;
                if (field.indexOf(CONVERSION_GOAL_FIELD_PREFIX) === 0) return; // skip conversion goal metrics
                columns.forEach(function (column) {
                    if (field !== column.field) return;
                    column.shown = true;
                    if (goal.conversion) {
                        column.name = goal.name + ' (' + goal.conversion + ')';
                    }
                });
            });
        });
    }

    return {
        COLUMNS: COLUMNS,
        createColumns: createColumns,
        createCategories: createCategories,
        updateConversionGoalColumns: updateConversionGoalColumns,
        updateOptimizationGoalColumns: updateOptimizationGoalColumns,
    };
}]);
