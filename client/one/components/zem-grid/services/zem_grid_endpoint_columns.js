/* globals oneApp, angular, constants */
'use strict';

oneApp.factory('zemGridEndpointColumns', ['zemGridConstants', function (zemGridConstants) {
    var CONVERSION_GOAL_FIELD_PREFIX = 'conversion_goal_';
    var AVG_COST_PER_CONVERSION_GOAL_PREFIX = 'avg_cost_per_conversion_goal_';

    // //////////////////////////////////////////////////////////////////////////////////////////////////
    // COLUMN DEFINITIONS
    //
    var COLUMNS = {
        id: {
            shown: false, // not shown (used internally)
            name: 'Id',
            field: 'id',
            type: zemGridConstants.gridColumnTypes.TEXT,
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
        state: {
            name: '', // Branded based on breakdown
            help: '', // Branded based on breakdown
            field: 'state',
            type: zemGridConstants.gridColumnTypes.STATE_SELECTOR,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.ASC,
            internal: false,
            shown: true,
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
            internal: 'zemauth.campaign_goal_performance',
            shown: 'zemauth.campaign_goal_performance',
        },

        agency: {
            name: 'Agency',
            field: 'agency',
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
            type: zemGridConstants.gridColumnTypes.TEXT,
            totalRow: false,
            help: 'Type of account.',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_see_account_type',
            shown: 'zemauth.can_see_account_type',
        },

        // Media source
        minBidCpc: {
            name: 'Min Bid',
            field: 'min_bid_cpc',
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
            type: zemGridConstants.gridColumnTypes.ICON_LINK,
            totalRow: false,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.supply_dash_link_view',
            shown: 'zemauth.supply_dash_link_view',
        },

        // AdGroup Media Sources
        bidCpcSetting: {
            name: 'Bid CPC',
            field: 'bid_cpc',
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            shown: true,
            fractionSize: 3,
            help: 'Maximum bid price (in USD) per click.',
            totalRow: false,
            order: true,
            editable: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
        dailyBudgetSetting: {
            name: 'Daily Budget',
            field: 'daily_budget',
            fractionSize: 0,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            shown: true,
            help: 'Maximum budget per day.',
            totalRow: true,
            order: true,
            editable: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
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
            help: 'Content ad\'s label.',
            totalRow: false,
            titleField: 'label',
            order: true,
            orderField: 'label',
            initialOrder: zemGridConstants.gridColumnOrder.ASC,
        },

        // Publisher
        externalId: {
            shown: false, // not shown (used internally)
            name: 'External Id',
            field: 'external_id',
            type: zemGridConstants.gridColumnTypes.TEXT,
        },
        sourceId: {
            shown: false, // not shown (used internally)
            name: 'Id',
            field: 'source_id',
            type: zemGridConstants.gridColumnTypes.TEXT,
        },
        domain: {
            name: 'Domain',
            field: 'domain',
            type: zemGridConstants.gridColumnTypes.TEXT,
            shown: true,
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
            help: 'Link to a publisher where your content is being promoted.',
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

        // Costs
        mediaCost: {
            name: 'Actual Media Spend',
            field: 'media_cost',
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
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            totalRow: true,
            help: 'Amount spent per media source.',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_view_platform_cost_breakdown',
            shown: 'zemauth.can_view_platform_cost_breakdown',
        },
        dataCost: {
            name: 'Actual Data Cost',
            field: 'data_cost',
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
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            totalRow: true,
            help: 'Additional targeting/segmenting costs.',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_view_platform_cost_breakdown',
            shown: 'zemauth.can_view_platform_cost_breakdown',
        },
        licenseFee: {
            name: 'License Fee',
            field: 'license_fee',
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            totalRow: true,
            help: 'Zemanta One platform usage cost.',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_view_platform_cost_breakdown',
            shown: 'zemauth.can_view_platform_cost_breakdown',
        },
        flatFee: {
            name: 'Recognized Flat Fee',
            field: 'flat_fee',
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            totalRow: true,
            help: 'Zemanta One fixed usage platform cost.',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_view_flat_fees',
            shown: ['zemauth.can_view_flat_fees', 'zemauth.can_view_platform_cost_breakdown'],
        },
        totalFee: {
            name: 'Total Fee',
            field: 'total_fee',
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            totalRow: true,
            help: 'Sum of License Fee and Recognized Flat Fee.',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_view_flat_fees',
            shown: ['zemauth.can_view_flat_fees', 'zemauth.can_view_platform_cost_breakdown'],
        },
        billingCost: {
            name: 'Total Spend',
            field: 'billing_cost',
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            totalRow: true,
            help: 'Sum of media spend, data cost and license fee.',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: false,
            shown: true,
        },
        margin: {
            name: 'Margin',
            field: 'margin',
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            totalRow: true,
            help: 'Agency\'s margin',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_view_agency_margin',
            shown: 'zemauth.can_view_agency_margin',
        },
        agencyTotal: {
            name: 'Total Spend + Margin',
            field: 'agency_total',
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            totalRow: true,
            help: 'Total billing cost including Media Spend, License Fee and Agency Margin',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_view_agency_margin',
            shown: 'zemauth.can_view_agency_margin',
        },
        cpc: {
            name: 'Avg. CPC',
            field: 'cpc',
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            shown: true,
            fractionSize: 3,
            help: 'The average CPC.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
        cpm: {
            name: 'Avg. CPM',
            field: 'cpm',
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            fractionSize: 3,
            help: 'Cost per 1,000 impressions.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            shown: true,
            internal: false,
        },

        // Yesterday cost metrics
        yesterdayCost: {
            name: 'Actual Yesterday Spend',
            field: 'yesterday_cost',
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
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            help: 'Amount that you have spent yesterday for promotion on specific ad group.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_view_platform_cost_breakdown',
            shown: 'zemauth.can_view_platform_cost_breakdown',
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
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            totalRow: true,
            help: '',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_see_projections',
            shown: ['zemauth.can_see_projections', 'zemauth.can_view_platform_cost_breakdown'],
        },
        pacing: {
            name: 'Pacing',
            field: 'pacing',
            type: zemGridConstants.gridColumnTypes.PERCENT,
            totalRow: true,
            help: '',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_see_projections',
            shown: ['zemauth.can_see_projections', 'zemauth.can_view_platform_cost_breakdown'],
        },
        spendProjection: {
            name: 'Spend Projection',
            field: 'spend_projection',
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            totalRow: true,
            help: '',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_see_projections',
            shown: ['zemauth.can_see_projections', 'zemauth.can_view_platform_cost_breakdown'],
        },
        licenseFeeProjection: {
            name: 'License Fee Projection',
            field: 'license_fee_projection',
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            totalRow: true,
            help: '',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_see_projections',
            shown: ['zemauth.can_see_projections', 'zemauth.can_view_platform_cost_breakdown'],
        },
        totalFeeProjection: {
            name: 'Total Fee Projection',
            field: 'total_fee_projection',
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            totalRow: true,
            help: 'Sum of License Fee Projection and Recognized Flat Fee.',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_see_projections',
            shown: ['zemauth.can_see_projections', 'zemauth.can_view_platform_cost_breakdown', 'zemauth.can_view_flat_fees'],
        },

        // Optimisation metrics
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
            help: 'Number of visitors that navigate to more than one page on the site.',
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
            help: 'Number of visitors that navigate to more than one page on the site.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
        avgCostPerMinute: {
            name: 'Avg. Cost per Minute',
            field: 'avg_cost_per_minute',
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            shown: true,
            internal: false,
            help: 'Average cost per minute spent on site.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
        avgCostPerPageview: {
            name: 'Avg. Cost per Pageview',
            field: 'avg_cost_per_pageview',
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            shown: true,
            internal: false,
            help: 'Average cost per pageview.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
        avgCostPerVisit: {
            name: 'Avg. Cost per Visit',
            field: 'avg_cost_per_visit',
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            shown: true,
            internal: false,
            help: 'Average cost per visit.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
        avgCostPerNonBouncedVisit: {
            name: 'Avg. Cost per Non-Bounced Visit',
            field: 'avg_cost_per_non_bounced_visit',
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            shown: true,
            internal: false,
            help: 'Average cost per non-bounced visit.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
        avgCostForNewVisitor: {
            name: 'Avg. Cost for New Visitor',
            field: 'avg_cost_for_new_visitor',
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            shown: true,
            internal: false,
            help: 'Average cost for new visitor.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },

        // Postclick Engagement Metrics
        percentNewUsers: {
            name: '% New Users',
            field: 'percent_new_users',
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
            type: zemGridConstants.gridColumnTypes.NUMBER,
            shown: 'zemauth.aggregate_postclick_acquisition',
            internal: 'zemauth.aggregate_postclick_acquisition',
            help: 'Total number of sessions within a date range. A session is the period of time in which a user ' +
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
            help: 'The total number of unique people who visited your site.',
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
            help: 'The total number of unique people who visited your site for the first time.',
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
            help: 'The total number of unique people who already visited your site in the past.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        },
        clickDiscrepancy: {
            name: 'Click Discrepancy',
            field: 'click_discrepancy',
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

    for (var i = 1; i <= 15; i++) {
        COLUMNS['conversionGoal' + i] = {
            name: 'Conversion Goal ' + i,
            field: CONVERSION_GOAL_FIELD_PREFIX + i,
            type: zemGridConstants.gridColumnTypes.NUMBER,
            help: 'Number of completions of the conversion goal',
            shown: false,
            internal: false,
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        };
    }

    for (i = 0; i < 16; i++) {
        COLUMNS['avgCostPerConversionGoal' + i] = {
            name: 'Avg. CPA',
            field: AVG_COST_PER_CONVERSION_GOAL_PREFIX + i,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            shown: false,
            internal: 'zemauth.campaign_goal_optimization',
            help: 'Average cost per acquisition.',
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        };
    }

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
        name: 'Title',
        help: 'The creative title/headline of a content ad. The link to landing page includes tracking codes.',
    };
    NAME_COLUMN_BRANDING[constants.breakdown.MEDIA_SOURCE] = {
        name: 'Media Source',
        help: 'A media source where your content is being promoted.',
    };
    NAME_COLUMN_BRANDING[constants.breakdown.PUBLISHER] = {
        name: 'Domain',
        help: 'A publisher where your content is being promoted.',
    };

    var STATUS_COLUMN_BRANDING = {};
    STATUS_COLUMN_BRANDING[constants.breakdown.ACCOUNT] = {
        name: 'Status',
        help: 'Status of an account (enabled or paused). An account is paused only if all its campaigns ' +
        'are paused too; otherwise the account is enabled.',
    };
    STATUS_COLUMN_BRANDING[constants.breakdown.CAMPAIGN] = {
        name: 'Status',
        help: 'Status of a campaign (enabled or paused). A campaign is paused only if all its ad groups ' +
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
        COLUMNS.id,
        COLUMNS.state,
        COLUMNS.name,
        COLUMNS.status,
        COLUMNS.submissionStatus,
        COLUMNS.performance,
    ];

    // Default columns - columns present by default (non permanent can be hidden)
    var DEFAULT_COLUMNS_GROUP = PERMANENT_COLUMNS_GROUP.concat([
        COLUMNS.imageUrls,
        COLUMNS.dailyBudget,
        COLUMNS.yesterdayCost,
        COLUMNS.eYesterdayCost,
        COLUMNS.billingCost,
        COLUMNS.clicks,
        COLUMNS.cpc,
    ]);

    var ACCOUNT_MANAGEMENT_GROUP = [
        COLUMNS.agency,
        COLUMNS.accountType,
        COLUMNS.defaultSalesRepresentative,
        COLUMNS.defaultAccountManager,
    ];

    var CAMPAIGN_MANAGEMENT_GROUP = [
        COLUMNS.campaignManager,
    ];

    var SOURCE_GROUP = [
        COLUMNS.minBidCpc,
        COLUMNS.maxBidCpc,
        COLUMNS.dailyBudget,
        COLUMNS.supplyDashUrl,
        COLUMNS.bidCpcSetting,
        COLUMNS.dailyBudgetSetting,
    ];

    var PUBLISHER_GROUP = [
        COLUMNS.sourceId,
        COLUMNS.externalId,
        COLUMNS.domain,
        COLUMNS.domainLink,
        COLUMNS.exchange,
    ];

    var CONTENT_GROUP = [
        COLUMNS.imageUrls,
        COLUMNS.urlLink,
        COLUMNS.displayUrl,
        COLUMNS.brandName,
        COLUMNS.description,
        COLUMNS.callToAction,
        COLUMNS.label,
        // TODO: impression trackers
        COLUMNS.uploadTime,
        COLUMNS.batchId,
        COLUMNS.batchName,
    ];

    var COSTS_GROUP = [
        COLUMNS.yesterdayCost,
        COLUMNS.eYesterdayCost,
        COLUMNS.mediaCost,
        COLUMNS.eMediaCost,
        COLUMNS.dataCost,
        COLUMNS.eDataCost,
        COLUMNS.licenseFee,
        COLUMNS.flatFee,
        COLUMNS.totalFee,
        COLUMNS.billingCost,
        COLUMNS.margin,
        COLUMNS.agencyTotal,
    ];

    var PROJECTIONS_GROUP = [
        COLUMNS.allocatedBudgets,
        COLUMNS.pacing,
        COLUMNS.spendProjection,
        COLUMNS.licenseFeeProjection,
        COLUMNS.totalFeeProjection,
    ];

    var TRAFFIC_ACQUISITION_GROUP = [
        COLUMNS.impressions,
        COLUMNS.clicks,
        COLUMNS.ctr,
        COLUMNS.cpc,
        COLUMNS.cpm,
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
    ];

    var CONVERSIONS_GROUP = [
        COLUMNS.conversionGoal1,
        COLUMNS.conversionGoal2,
        COLUMNS.conversionGoal3,
        COLUMNS.conversionGoal4,
        COLUMNS.conversionGoal5,
        COLUMNS.conversionGoal6,
        COLUMNS.conversionGoal7,
        COLUMNS.conversionGoal8,
        COLUMNS.conversionGoal9,
        COLUMNS.conversionGoal10,
        COLUMNS.conversionGoal11,
        COLUMNS.conversionGoal12,
        COLUMNS.conversionGoal13,
        COLUMNS.conversionGoal14,
        COLUMNS.conversionGoal15,
    ];

    var CAMPAIGN_GOALS_GROUP = [
        COLUMNS.avgCostPerVisit,
        COLUMNS.avgCostForNewVisitor,
        COLUMNS.avgCostPerPageview,
        COLUMNS.avgCostPerNonBouncedVisit,
        COLUMNS.avgCostPerMinute,
        COLUMNS.avgCostPerConversionGoal0,
        COLUMNS.avgCostPerConversionGoal1,
        COLUMNS.avgCostPerConversionGoal2,
        COLUMNS.avgCostPerConversionGoal3,
        COLUMNS.avgCostPerConversionGoal4,
        COLUMNS.avgCostPerConversionGoal5,
        COLUMNS.avgCostPerConversionGoal6,
        COLUMNS.avgCostPerConversionGoal7,
        COLUMNS.avgCostPerConversionGoal8,
        COLUMNS.avgCostPerConversionGoal9,
        COLUMNS.avgCostPerConversionGoal10,
        COLUMNS.avgCostPerConversionGoal11,
        COLUMNS.avgCostPerConversionGoal12,
        COLUMNS.avgCostPerConversionGoal13,
        COLUMNS.avgCostPerConversionGoal14,
        COLUMNS.avgCostPerConversionGoal15,
    ];

    var METRICS_GROUP = [].concat(
        COSTS_GROUP,
        PROJECTIONS_GROUP,
        TRAFFIC_ACQUISITION_GROUP,
        AUDIENCE_METRICS_GROUP,
        CONVERSIONS_GROUP,
        CAMPAIGN_GOALS_GROUP
    );

    // //////////////V////////////////////////////////////////////////////////////////////////////////////
    //  COLUMNS CONFIGURATION (order, availability, ...)
    //

    // Sets order of columns (this collection is used for creation)
    var COLUMNS_ORDERED = [].concat(
        PERMANENT_COLUMNS_GROUP,
        ACCOUNT_MANAGEMENT_GROUP,
        CAMPAIGN_MANAGEMENT_GROUP,
        CONTENT_GROUP,
        SOURCE_GROUP,
        PUBLISHER_GROUP,
        METRICS_GROUP
    );

    // Configure special column properties
    PERMANENT_COLUMNS_GROUP.forEach(function (column) { column.permanent = true; });
    DEFAULT_COLUMNS_GROUP.forEach(function (column) { column.default = true; });
    CAMPAIGN_GOALS_GROUP.forEach(function (column) { column.goal = true; });

    // Configuration (availability based on breakdown)
    configureBreakdowns(ACCOUNT_MANAGEMENT_GROUP, [constants.breakdown.ACCOUNT]);
    configureBreakdowns(CAMPAIGN_MANAGEMENT_GROUP, [constants.breakdown.CAMPAIGN]);
    configureBreakdowns(CONTENT_GROUP, [constants.breakdown.CONTENT_AD]);
    configureBreakdowns(SOURCE_GROUP, [constants.breakdown.MEDIA_SOURCE]);
    configureBreakdowns(PUBLISHER_GROUP, [constants.breakdown.PUBLISHER]);
    configureBreakdowns(
        [COLUMNS.yesterdayCost, COLUMNS.eYesterdayCost],
        [constants.breakdown.CAMPAIGN, constants.breakdown.AD_GROUP, constants.breakdown.MEDIA_SOURCE]
    );

    // Configuration (availability based on level)
    configureLevels(PROJECTIONS_GROUP, [constants.level.ALL_ACCOUNTS, constants.level.ACCOUNTS]);

    // Exceptions (state - not yet supported everywhere, only available on base level)
    COLUMNS.state.breakdowns = [constants.breakdown.AD_GROUP, constants.breakdown.CONTENT_AD, constants.breakdown.MEDIA_SOURCE];
    COLUMNS.state.breakdownBaseLevelOnly = true;

    // Exceptions (submission status - only shown on AD_GROUPS level for CONTENT_AD breakdown)
    COLUMNS.submissionStatus.breakdowns = [constants.breakdown.CONTENT_AD];
    COLUMNS.submissionStatus.levels = [constants.level.AD_GROUPS];

    // Exceptions (performance - not shown on ALL_ACCOUNTS level)
    COLUMNS.performance.levels = [constants.level.ACCOUNTS, constants.level.CAMPAIGNS, constants.level.AD_GROUPS];

    // Exceptions (total fee and recognized flat fee - only shown on ALL_ACCOUNTS level)
    COLUMNS.totalFee.levels = [constants.level.ALL_ACCOUNTS];
    COLUMNS.flatFee.levels = [constants.level.ALL_ACCOUNTS];

    // Exceptions (total fee projection - only shown on ALL_ACCOUNTS level)
    COLUMNS.totalFeeProjection.levels = [constants.level.ALL_ACCOUNTS];

    // Exceptions (supply dash url - only shown on AD_GROUPS level on base row level)
    COLUMNS.supplyDashUrl.levels = [constants.level.AD_GROUPS];
    COLUMNS.supplyDashUrl.breakdownBaseLevelOnly = true;

    // Exceptions (source editable fields)
    COLUMNS.minBidCpc.levels = [constants.level.ALL_ACCOUNTS, constants.level.ACCOUNTS, constants.level.CAMPAIGNS];
    COLUMNS.maxBidCpc.levels = [constants.level.ALL_ACCOUNTS, constants.level.ACCOUNTS, constants.level.CAMPAIGNS];
    COLUMNS.dailyBudget.levels = [constants.level.ALL_ACCOUNTS, constants.level.ACCOUNTS, constants.level.CAMPAIGNS];
    COLUMNS.bidCpcSetting.levels = [constants.level.AD_GROUPS];
    COLUMNS.dailyBudgetSetting.levels = [constants.level.AD_GROUPS];
    COLUMNS.bidCpcSetting.breakdownBaseLevelOnly = true;
    COLUMNS.dailyBudgetSetting.breakdownBaseLevelOnly = true;

    function configureBreakdowns (columns, breakdowns) {
        columns.forEach(function (column) {
            column.breakdowns = breakdowns;
        });
    }

    function configureLevels (columns, levels) {
        columns.forEach(function (column) {
            column.levels = levels;
        });
    }

    // ///////////////////////////////////////////////////////////////////////////////////////////////////
    //  COLUMN CATEGORIES
    //
    var CATEGORIES = [
        {
            name: 'Management',
            columns: [].concat(ACCOUNT_MANAGEMENT_GROUP, CAMPAIGN_MANAGEMENT_GROUP),
        },
        {
            name: 'Content Sync',
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
            name: 'Costs',
            columns: COSTS_GROUP,
        },
        {
            name: 'Projections',
            columns: PROJECTIONS_GROUP,
        },
        {
            name: 'Traffic Acquisition',
            columns: TRAFFIC_ACQUISITION_GROUP,
        },
        {
            name: 'Audience Metrics',
            columns: AUDIENCE_METRICS_GROUP,
        },
        {
            name: 'Conversions',
            columns: CONVERSIONS_GROUP,
        },
        {
            name: 'Goals',
            columns: CAMPAIGN_GOALS_GROUP,
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

    function brandColumns (columns, breakdown) {
        function findColumn (column) {
            return columns.filter(function (c) { return column.field === c.field; })[0];
        }

        var nameColumn = findColumn(COLUMNS.name);
        nameColumn.name = NAME_COLUMN_BRANDING[breakdown].name;
        nameColumn.help = NAME_COLUMN_BRANDING[breakdown].help;

        var statusColumn = findColumn(COLUMNS.status);
        statusColumn.name = STATUS_COLUMN_BRANDING[breakdown].name;
        statusColumn.help = STATUS_COLUMN_BRANDING[breakdown].help;

        var stateColumn = findColumn(COLUMNS.state);
        if (stateColumn) {
            stateColumn.name = STATE_COLUMN_BRANDING[breakdown].name;
            stateColumn.help = STATE_COLUMN_BRANDING[breakdown].help;
        }
    }

    function intersects (array1, array2) {
        // Simple solution for finding if arrays are having common element
        return array1.filter(function (n) {
            return array2.indexOf(n) != -1;
        }).length > 0;
    }

    function getColumns (level, breakdowns) {
        return COLUMNS_ORDERED.filter(function (column) {
            var result = true;
            if (column.breakdowns) result &= intersects(column.breakdowns, breakdowns);
            if (column.breakdownBaseLevelOnly) result &= column.breakdowns.indexOf(breakdowns[0]) >= 0;
            if (column.levels) result &= column.levels.indexOf(level) >= 0;

            // FIXME: Find a better solution for columns thet are shown only in certain breakdown-level combinations
            // State selector is only shown on CAMPAIGNS level for AD_GROUP breakdown and not for MEDIA_SOURCE
            // breakdown
            if (column === COLUMNS.state && breakdowns[0] === constants.breakdown.MEDIA_SOURCE) {
                result &= level === constants.level.AD_GROUPS;
            }

            // Projections for MEDIA_SOURCE breakdown are only shown on ALL_ACCOUNTS level
            if (PROJECTIONS_GROUP.indexOf(column) >= 0 && breakdowns[0] === constants.breakdown.MEDIA_SOURCE) {
                result &= level === constants.level.ALL_ACCOUNTS;
            }

            return result;
        });
    }

    function createColumns ($scope, level, breakdowns) {
        // Create columns definitions array based on base level and breakdown
        var columns = angular.copy(getColumns(level, breakdowns));
        checkPermissions($scope, columns);
        brandColumns(columns, breakdowns[0]);
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
                    column.default = goal.primary; // primary goal visible by default
                    if (goal.conversion) {
                        column.name = goal.name + ' (' + goal.conversion + ')';
                    }
                });
            });
        });
    }

    function findColumnByField (field) {
        if (!findColumnByField.cache) {
            findColumnByField.cache = {};
            angular.forEach(COLUMNS, function (column) {
                findColumnByField.cache[column.field] = column;
            });
        }
        return findColumnByField.cache[field];
    }

    return {
        COLUMNS: COLUMNS,
        findColumnByField: findColumnByField,
        createColumns: createColumns,
        createCategories: createCategories,
        updateConversionGoalColumns: updateConversionGoalColumns,
        updateOptimizationGoalColumns: updateOptimizationGoalColumns,
    };
}]);
