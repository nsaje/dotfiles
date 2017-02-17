/* globals angular, constants, options */
'use strict';

angular.module('one.widgets').factory('zemGridEndpointColumns', function (zemPermissions, zemGridConstants) {
    var AVG_COST_PREFIX = 'avg_cost_per_';

    var CONVERSION_GOALS_PLACEHOLDER = 'conversion_goals_placeholder';
    var PIXELS_PLACEHOLDER = 'pixels_placeholder';

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
        editButton: {
            name: '',
            help: '',
            field: 'editButton',
            type: zemGridConstants.gridColumnTypes.EDIT_BUTTON,
            order: false,
            internal: 'zemauth.can_edit_content_ads',
            shown: 'zemauth.can_edit_content_ads',
            totalRow: false,
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
        defaultCsRepresentative: {
            name: 'CS Representative',
            field: 'default_cs_representative',
            type: zemGridConstants.gridColumnTypes.TEXT,
            totalRow: false,
            help: 'Customer Success representative responsible for the campaign and the communication with the client.',
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
            defaultValue: '',
        },
        dailyBudgetSetting: {
            name: 'Daily Spend Cap',
            field: 'daily_budget',
            fractionSize: 0,
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            shown: true,
            help: 'Maximum media spend cap per day.',
            totalRow: true,
            order: true,
            editable: true,
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
            help: 'The ideal media budget available for selected date range.',
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
            help: 'Media spend divided by ideal media budget for selected date range.',
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
            help: 'Predicted media and data spend by the end of ' +
                  'selected date range based on the spend in the previous days.',
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
            help: 'Predicted license fee by the end of selected date range based on the ' +
                    'license fee in the previous days.',
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
            help: 'Predicted total fee by the end of selected date range based on the ' +
                    'license fee in the previous days and recognized flat fee.',
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            internal: 'zemauth.can_see_projections',
            shown: ['zemauth.can_see_projections', 'zemauth.can_view_platform_cost_breakdown', 'zemauth.can_view_flat_fees'], // eslint-disable-line max-len
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
            help: 'The average cost per minute that visitors spent on your site. Only visitors responding to an ad are included. <br />Average cost per minute spent on site.', // eslint-disable-line max-len
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            goal: true,
        },
        avgCostPerPageview: {
            name: 'Avg. Cost per Pageview',
            field: 'avg_cost_per_pageview',
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            shown: true,
            internal: false,
            help: 'The average cost per pageview on your site. Only pageviews generated by visitors responding to an ad are included. <br />The metric is calculated as the total amount of pageviews divided by total cost.', // eslint-disable-line max-len
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            goal: true,
        },
        avgCostPerVisit: {
            name: 'Avg. Cost per Visit',
            field: 'avg_cost_per_visit',
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            shown: true,
            internal: false,
            help: 'The average cost per visit to your site. Only visits generated by visitors responding to an ad are included. <br />Visits are detected by your analytics software (Google Analytics or Adobe Omniture) as opposed to clicks, which are detected by Zemanta. They provide a better insight into the value of traffic sent by Zemanta. <br />The metric is calculated as the total amount of visits divided by total cost.', // eslint-disable-line max-len
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
            goal: true,
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
            goal: true,
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
            goal: true,
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
        conversionCpa: {
            type: zemGridConstants.gridColumnTypes.CURRENCY,
            help: 'Average cost per acquisition.',
            shown: false,
            internal: false,
            totalRow: true,
            order: true,
            initialOrder: zemGridConstants.gridColumnOrder.DESC,
        }
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
        help: 'The creative title/headline of a content ad. The link to landing page includes tracking codes.',
    };
    NAME_COLUMN_BRANDING[constants.breakdown.MEDIA_SOURCE] = {
        name: 'Media Source',
        help: 'A media source where your content is being promoted.',
    };
    NAME_COLUMN_BRANDING[constants.breakdown.PUBLISHER] = {
        name: 'Publisher',
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
        COLUMNS.editButton,
        COLUMNS.name,
        COLUMNS.exchange,
        COLUMNS.status,
        COLUMNS.submissionStatus,
        COLUMNS.performance,
        COLUMNS.bidCpcSetting,
        COLUMNS.dailyBudgetSetting,
    ];

    // Default columns - columns present by default (non permanent can be hidden)
    var DEFAULT_COLUMNS_GROUP = PERMANENT_COLUMNS_GROUP.concat([
        COLUMNS.imageUrls,
        COLUMNS.eYesterdayCost,
        COLUMNS.billingCost,
        COLUMNS.allocatedBudgets,
        COLUMNS.pacing,
        COLUMNS.spendProjection,
        COLUMNS.clicks,
        COLUMNS.cpc,
    ]);

    var ACCOUNT_MANAGEMENT_GROUP = [
        COLUMNS.agency,
        COLUMNS.accountType,
        COLUMNS.defaultSalesRepresentative,
        COLUMNS.defaultCsRepresentative,
        COLUMNS.defaultAccountManager,
        COLUMNS.salesforceUrl,
    ];

    var CAMPAIGN_MANAGEMENT_GROUP = [
        COLUMNS.campaignManager,
    ];

    var SOURCE_GROUP = [
        COLUMNS.supplyDashUrl,
    ];

    var PUBLISHER_GROUP = [
        COLUMNS.sourceId,
        COLUMNS.externalId,
        COLUMNS.domain,
        COLUMNS.domainLink,
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
        COLUMNS.avgCostPerVisit,
        COLUMNS.avgCostForNewVisitor,
        COLUMNS.avgCostPerPageview,
        COLUMNS.avgCostPerNonBouncedVisit,
        COLUMNS.avgCostPerMinute,
    ];

    var PIXELS_GROUP = [
        COLUMNS.pixelsPlaceholder,
    ];

    var CONVERSION_GOALS_GROUP = [
        COLUMNS.conversionGoalsPlaceholder,
    ];

    var METRICS_GROUP = [].concat(
        COSTS_GROUP,
        PROJECTIONS_GROUP,
        TRAFFIC_ACQUISITION_GROUP,
        AUDIENCE_METRICS_GROUP,
        PIXELS_GROUP,
        CONVERSION_GOALS_GROUP
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

    // Exceptions object
    COLUMNS_ORDERED.forEach(function (column) {
        column.exceptions = {
            levels: undefined,     // levels where this column is available; defaults to ALL
            breakdowns: undefined, // breakdowns where this column is available; defaults to ALL
            breakdownBaseLevelOnly: false, // column only available on base level (level 1)
            custom: [],            // custom exceptions -> level/breakdown pairs; overwrites previous properties
        };
    });

    // Configuration (availability based on breakdown)
    configureBreakdownExceptions(ACCOUNT_MANAGEMENT_GROUP, [constants.breakdown.ACCOUNT]);
    configureBreakdownExceptions(CAMPAIGN_MANAGEMENT_GROUP, [constants.breakdown.CAMPAIGN]);
    configureBreakdownExceptions(CONTENT_GROUP, [constants.breakdown.CONTENT_AD]);
    configureBreakdownExceptions(SOURCE_GROUP, [constants.breakdown.MEDIA_SOURCE]);
    configureBreakdownExceptions(PUBLISHER_GROUP, [constants.breakdown.PUBLISHER]);

    // Exceptions (Projections) - ALL_ACCOUNTS, ACCOUNTS level, MEDIA_SOURCE
    // breakdown are only shown on ALL_ACCOUNTS level
    configureLevelExceptions(PROJECTIONS_GROUP, [constants.level.ALL_ACCOUNTS, constants.level.ACCOUNTS]);
    configureCustomException(PROJECTIONS_GROUP, {level: constants.level.ACCOUNTS, breakdown: constants.breakdown.MEDIA_SOURCE, shown: false}); // eslint-disable-line max-len

    // Exceptions (state - not yet supported everywhere, only available on base level)
    COLUMNS.state.exceptions.breakdowns = [constants.breakdown.AD_GROUP, constants.breakdown.CONTENT_AD];
    COLUMNS.state.exceptions.breakdownBaseLevelOnly = true;
    // State selector is only shown on MEDIA_SOURCE breakdown on AD_GROUPS level
    COLUMNS.state.exceptions.custom.push({level: constants.level.AD_GROUPS, breakdown: constants.breakdown.MEDIA_SOURCE, shown: true}); // eslint-disable-line max-len


    // Exceptions (edit button - only available on base content ad level)
    COLUMNS.editButton.exceptions.breakdowns = [constants.breakdown.CONTENT_AD];
    COLUMNS.editButton.exceptions.levels = [constants.level.AD_GROUPS];
    COLUMNS.editButton.exceptions.breakdownBaseLevelOnly = true;

    // Exceptions (submission status - only shown on AD_GROUPS level for CONTENT_AD breakdown)
    COLUMNS.submissionStatus.exceptions.breakdowns = [constants.breakdown.CONTENT_AD];
    COLUMNS.submissionStatus.exceptions.levels = [constants.level.AD_GROUPS];

    COLUMNS.exchange.exceptions.breakdowns = [constants.breakdown.PUBLISHER];

    // Exceptions (performance - not shown on ALL_ACCOUNTS level and on ACCOUNT - MEDIA SOURCES)
    COLUMNS.performance.exceptions.levels = [constants.level.ACCOUNTS, constants.level.CAMPAIGNS, constants.level.AD_GROUPS]; // eslint-disable-line max-len
    COLUMNS.performance.exceptions.custom.push({level: constants.level.ACCOUNTS, breakdown: constants.breakdown.MEDIA_SOURCE, shown: false}); // eslint-disable-line max-len

    // Exceptions (media source status column - shown only on Ad Group level)
    COLUMNS.status.exceptions.custom.push({level: constants.level.ALL_ACCOUNTS, breakdown: constants.breakdown.MEDIA_SOURCE, shown: false}); // eslint-disable-line max-len
    COLUMNS.status.exceptions.custom.push({level: constants.level.ACCOUNTS, breakdown: constants.breakdown.MEDIA_SOURCE, shown: false}); // eslint-disable-line max-len
    COLUMNS.status.exceptions.custom.push({level: constants.level.CAMPAIGNS, breakdown: constants.breakdown.MEDIA_SOURCE, shown: false}); // eslint-disable-line max-len

    // Exceptions (total fee and recognized flat fee - only shown on ALL_ACCOUNTS level)
    COLUMNS.totalFee.exceptions.levels = [constants.level.ALL_ACCOUNTS];
    COLUMNS.flatFee.exceptions.levels = [constants.level.ALL_ACCOUNTS];

    // Exceptions (total fee projection - only shown on ALL_ACCOUNTS level)
    COLUMNS.totalFeeProjection.exceptions.levels = [constants.level.ALL_ACCOUNTS];

    // Exceptions (supply dash url - only shown on AD_GROUPS level on base row level)
    COLUMNS.supplyDashUrl.exceptions.levels = [constants.level.AD_GROUPS];
    COLUMNS.supplyDashUrl.exceptions.breakdownBaseLevelOnly = true;

    // Exceptions (source editable fields)
    COLUMNS.bidCpcSetting.exceptions.breakdowns = [constants.breakdown.MEDIA_SOURCE];
    COLUMNS.dailyBudgetSetting.exceptions.breakdowns = [constants.breakdown.MEDIA_SOURCE];
    COLUMNS.bidCpcSetting.exceptions.levels = [constants.level.AD_GROUPS];
    COLUMNS.dailyBudgetSetting.exceptions.levels = [constants.level.AD_GROUPS];
    COLUMNS.bidCpcSetting.exceptions.breakdownBaseLevelOnly = true;
    COLUMNS.dailyBudgetSetting.exceptions.breakdownBaseLevelOnly = true;


    function configureBreakdownExceptions (columns, breakdowns) {
        columns.forEach(function (column) {
            column.exceptions.breakdowns = breakdowns;
        });
    }

    function configureLevelExceptions (columns, levels) {
        columns.forEach(function (column) {
            column.exceptions.levels = levels;
        });
    }

    function configureCustomException (columns, customException) {
        columns.forEach(function (column) {
            column.exceptions.custom.push(customException);
        });
    }

    // ///////////////////////////////////////////////////////////////////////////////////////////////////
    //  COLUMN CATEGORIES
    //
    var CONVERSIONS_CATEGORY = 'Conversions & CPAs';
    var CATEGORIES = [
        {
            name: 'Management',
            columns: [].concat(ACCOUNT_MANAGEMENT_GROUP, CAMPAIGN_MANAGEMENT_GROUP),
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
            name: CONVERSIONS_CATEGORY,
            description: 'Choose conversion window in days.',
            columns: PIXELS_GROUP,
        },
        {
            name: 'Google & Adobe Analytics Goals',
            columns: CONVERSION_GOALS_GROUP,
        }
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

    function checkPermissions (columns) {
        // Go trough all columns and convert permissions to boolean, when needed
        columns.forEach(function (column) {
            column.internal = convertPermission(column.internal, zemPermissions.isPermissionInternal);
            column.shown = convertPermission(column.shown, zemPermissions.hasPermission);
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
        if (statusColumn) {
            statusColumn.name = STATUS_COLUMN_BRANDING[breakdown].name;
            statusColumn.help = STATUS_COLUMN_BRANDING[breakdown].help;
        }

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
            if (column.exceptions.breakdowns) result = result && intersects(column.exceptions.breakdowns, breakdowns);
            if (column.exceptions.breakdownBaseLevelOnly) result = result && column.exceptions.breakdowns.indexOf(breakdowns[0]) >= 0; // eslint-disable-line max-len
            if (column.exceptions.levels) result = result && column.exceptions.levels.indexOf(level) >= 0;
            column.exceptions.custom.forEach(function (customException) {
                if (level === customException.level && breakdowns[0] === customException.breakdown) {
                    result = customException.shown;
                }
            });
            return result;
        });
    }

    function createColumns (level, breakdowns) {
        // Create columns definitions array based on base level and breakdown
        var columns = angular.copy(getColumns(level, breakdowns));
        checkPermissions(columns);
        brandColumns(columns, breakdowns[0]);
        return columns;
    }

    function createCategories () {
        return CATEGORIES.map(function (category) {
            var fields = category.columns.map(function (column) {
                return column.field;
            });
            var ret = {
                name: category.name,
                fields: fields,
            };

            if (category.description) ret.description = category.description;
            return ret;
        });
    }

    function insertIntoColumns (columns, newColumns, placeholder) {
        var columnPosition = findColumnPosition(columns, placeholder);
        if (!columnPosition) return;

        Array.prototype.splice.apply(columns, [columnPosition, 0].concat(newColumns));
    }

    function insertIntoCategories (categories, newFields, placeholder) {
        var categoryPosition = findCategoryPosition(categories, placeholder);
        if (!categoryPosition) return;

        Array.prototype.splice.apply(categoryPosition.fields, [categoryPosition.position, 0].concat(newFields));
    }

    function setPrimaryCampaignGoal (columns, campaignGoals) {
        if (!campaignGoals) return;

        campaignGoals.forEach(function (goal) {
            angular.forEach(goal.fields, function (shown, field) {
                if (!shown) return;
                if (!goal.primary) return;
                columns.forEach(function (column) {
                    if (field !== column.field) return;
                    column.default = true;
                });
            });
        });
    }

    function setPixelColumns (columns, categories, pixels) {
        var orderedColumns = [];
        var category = findCategoryByName(categories, CONVERSIONS_CATEGORY);
        if (!category) return;

        category.subcategories = [];
        angular.forEach(pixels, function (pixel) {
            var subcategory = {
                name: pixel.name,
                fields: [],
                type: 'condensed',
            };
            category.subcategories.push(subcategory);
            angular.forEach(options.conversionWindows, function (window) {
                var name = pixel.name + ' ' + window.name;
                var conversionsField = pixel.prefix + '_' + window.value;
                var conversionsCol = angular.copy(COLUMNS.conversionCount);
                conversionsCol.name = name;
                conversionsCol.shortName = window.value / 24;
                conversionsCol.field = conversionsField;
                conversionsCol.shown = true;

                var cpaName = 'CPA (' + name + ')';
                var cpaField = AVG_COST_PREFIX + conversionsField;
                var cpaCol = angular.copy(COLUMNS.conversionCpa);
                cpaCol.name = cpaName;
                cpaCol.field = cpaField;
                cpaCol.shown = true;
                cpaCol.autoSelect = conversionsField;
                cpaCol.goal = true;

                subcategory.fields.push(conversionsField);
                orderedColumns.push(conversionsCol);
                orderedColumns.push(cpaCol);
            });
        });

        insertIntoColumns(columns, orderedColumns, PIXELS_PLACEHOLDER);
    }

    function setConversionGoalColumns (columns, categories, conversionGoals) {
        if (!conversionGoals) return;

        var orderedColumns = [],
            newFields = [];
        angular.forEach(conversionGoals, function (goal) {
            var conversionsCol = angular.copy(COLUMNS.conversionCount);
            conversionsCol.name = goal.name;
            conversionsCol.field = goal.id;
            conversionsCol.shown = true;

            var cpaCol = angular.copy(COLUMNS.conversionCpa);
            cpaCol.name = 'CPA (' + goal.name + ')';
            cpaCol.field = AVG_COST_PREFIX + goal.id;
            cpaCol.shown = true;
            cpaCol.goal = true;

            newFields.push(conversionsCol.field);
            newFields.push(cpaCol.field);

            orderedColumns.push(conversionsCol);
            orderedColumns.push(cpaCol);
        });

        insertIntoColumns(columns, orderedColumns, CONVERSION_GOALS_PLACEHOLDER);
        insertIntoCategories(categories, newFields, CONVERSION_GOALS_PLACEHOLDER);
    }

    function setDynamicColumns (columns, categories, campaignGoals, conversionGoals, pixels) {
        setPixelColumns(columns, categories, pixels);
        setConversionGoalColumns(columns, categories, conversionGoals);
        setPrimaryCampaignGoal(columns, campaignGoals);
    }

    function findCategoryByName (categories, name) {
        for (var i = 0; i < categories.length; i++) {
            if (categories[i].name === name) {
                return categories[i];
            }
        }
    }

    function findColumnPosition (columns, field) {
        for (var i = 0; i < columns.length; i++) {
            if (columns[i].field === field) {
                // return next index
                return i + 1;
            }
        }
    }

    function findCategoryPosition (categories, field) {
        for (var i = 0; i < categories.length; i++) {
            for (var j = 0; j < categories[i].fields.length; j++) {
                if (categories[i].fields[j] === field) {
                    return {
                        fields: categories[i].fields,
                        position: j + 1 // return next index
                    };
                }
            }
        }
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
        setDynamicColumns: setDynamicColumns,
    };
});
