/* globals oneApp, angular */
'use strict';

oneApp.factory('zemGridEndpointColumns', ['$rootScope', '$controller', '$http', '$q', function ($rootScope, $controller, $http, $q) { // eslint-disable-line max-len
    // removed extraTdCss
    // TODO: conversion goals, metrics, ..
    // TODO: default values : unselectable, checked, shown, totalRow, order, orderField==field, initialOrder
    // TODO: column merging - status, state, ...

    // TODO - actions - clickCallback: zemFilterService.exclusivelyFilterSource

    // TODO: state - saveData, constants, messages, archived - move to directives
    // TODO: settings - saveData, constants, autopilotOn
    // FIXME: Categories -- Diff conflict in ad_group_publishers

    // //////////////////////////////////////////////////////////////////////////////////////////////////
    //  COLUMN DEFINITIONS
    // //////////////////////////////////////////////////////////////////////////////////////////////////

    var COLUMNS = {
        account: {
            name: 'Account',
            field: 'name_link',
            unselectable: true,
            checked: true,
            type: 'linkNav',
            shown: true,
            totalRow: false,
            help: 'A partner account.',
            order: true,
            orderField: 'name',
            initialOrder: 'asc',
        },
        campaign: {
            name: 'Campaign',
            field: 'name',
            unselectable: true,
            checked: true,
            type: 'linkNav',
            shown: true,
            totalRow: false,
            help: 'Name of the campaign.',
            order: true,
            initialOrder: 'asc',
        },
        adgroup: {
            name: 'Ad Group',
            field: 'name',
            unselectable: true,
            checked: true,
            type: 'linkNav',
            shown: true,
            totalRow: false,
            help: 'Name of the ad group.',
            order: true,
            initialOrder: 'asc',
        },
        mediaSource: {
            name: 'Media Source',
            field: 'name',
            unselectable: true,
            checked: true,
            type: 'clickPermissionOrText',
            totalRow: false,
            help: 'A media source where your content is being promoted.',
            order: true,
            initialOrder: 'asc',
            hasPermission: 'zemauth.can_filter_sources_through_table',
            shown: true,
        },
        agency: {
            name: 'Agency',
            field: 'agency',
            unselectable: true,
            checked: true,
            type: 'text',
            totalRow: false,
            help: 'Agency to which this account belongs.',
            order: true,
            initialOrder: 'desc',
            internal: 'zemauth.can_view_account_agency_information',
            shown: 'zemauth.can_view_account_agency_information',
        },
        defaultAccountManager: {
            name: 'Account Manager',
            field: 'default_account_manager',
            checked: false,
            type: 'text',
            totalRow: false,
            help: 'Account manager responsible for the campaign and the communication with the client.',
            order: true,
            initialOrder: 'desc',
            internal: 'zemauth.can_see_managers_in_accounts_table',
            shown: 'zemauth.can_see_managers_in_accounts_table',
        },
        defaultSalesRepresentative: {
            name: 'Sales Representative',
            field: 'default_sales_representative',
            checked: false,
            type: 'text',
            totalRow: false,
            help: 'Sales representative responsible for the campaign and the communication with the client.',
            order: true,
            initialOrder: 'desc',
            internal: 'zemauth.can_see_managers_in_accounts_table',
            shown: 'zemauth.can_see_managers_in_accounts_table',
        },
        campaignManager: {
            name: 'Campaign Manager',
            field: 'campaign_manager',
            checked: false,
            type: 'text',
            totalRow: false,
            help: 'Campaign manager responsible for the campaign and the communication with the client.',
            order: true,
            initialOrder: 'desc',
            internal: 'zemauth.can_see_managers_in_campaigns_table',
            shown: 'zemauth.can_see_managers_in_campaigns_table',
        },
        accountType: {
            name: 'Account Type',
            field: 'account_type',
            checked: false,
            type: 'text',
            totalRow: false,
            help: 'Type of account.',
            order: true,
            initialOrder: 'desc',
            internal: 'zemauth.can_see_account_type',
            shown: 'zemauth.can_see_account_type',
        },
        performance: {
            nameCssClass: 'performance-icon',
            field: 'performance',
            unselectable: true,
            checked: true,
            type: 'icon-list',
            totalRow: false,
            help: 'Goal performance indicator',
            order: true,
            initialOrder: 'asc',
            internal: 'zemauth.campaign_goal_performance',
            shown: 'zemauth.campaign_goal_performance',
        },

        // Status columns
        statusAccount: {
            name: 'Status',
            field: 'status',
            unselectable: true,
            checked: true,
            type: 'text',
            shown: true,
            totalRow: false,
            help: 'Status of an account (enabled or paused). An account is paused only if all its campaigns ' +
                  'are paused too; otherwise the account is enabled.',
            order: true,
            orderField: 'status',
            initialOrder: 'asc',
        },
        statusCampaign: {
            name: 'Status',
            field: 'state',
            checked: true,
            type: 'text',
            shown: true,
            totalRow: false,
            help: 'Status of a campaign (enabled or paused). A campaign is paused only if all its ad groups ' +
                  'are paused too; otherwise, the campaign is enabled.',
            order: true,
            initialOrder: 'asc',
        },
        statusAdGroup: {
            name: 'Status',
            field: 'stateText',
            unselectable: true,
            checked: true,
            type: 'text',
            shown: true,
            totalRow: false,
            help: 'Status of an ad group (enabled or paused).',
            order: true,
            initialOrder: 'asc',
        },
        statusContentAd: {
            name: 'Status',
            field: 'submission_status',
            checked: false,
            type: 'submissionStatus',
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
            type: 'text',
            shown: true,
            totalRow: false,
            help: 'Status of a particular media source (enabled or paused).',
            order: true,
            orderField: 'status',
            initialOrder: 'asc',
        },
        statusMediaSourceAdGroup: {
            name: 'Status',
            field: 'status',
            unselectable: true,
            checked: true,
            type: 'notification',
            shown: true,
            totalRow: false,
            help: 'Status of a particular media source (enabled or paused).',
            order: true,
            orderField: 'status',
            initialOrder: 'asc',
        },
        statusPublisher: {
            name: 'Status',
            field: 'blacklisted',
            checked: true,
            type: 'textWithPopup',
            popupField: 'blacklisted_level_description',
            help: 'Blacklisted status of a publisher.',
            totalRow: false,
            order: false,
            initialOrder: 'asc',
            shown: 'zemauth.can_see_publisher_blacklist_status',
        },

        // State TODO: refactor
        stateAdGroup: { // AdGroup state
            name: '\u25CF',
            field: 'state',
            type: 'state',
            order: true,
            editable: true,
            initialOrder: 'asc',
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
            type: 'state',
            order: true,
            initialOrder: 'asc',
            internal: false,
            shown: true,
            checked: true,
            totalRow: false,
            unselectable: true,
            help: 'A setting for enabling and pausing content ads.',
            disabled: false,
            archivedField: 'archived',
        },

        // AdGroup specials (Yesterday spends)
        yesterdayCost: {
            name: 'Actual Yesterday Spend',
            field: 'yesterday_cost',
            checked: false,
            type: 'currency',
            help: 'Amount that you have spent yesterday for promotion on specific ad group, including overspend.',
            totalRow: true,
            order: true,
            internal: 'zemauth.can_view_actual_costs',
            initialOrder: 'desc',
            shown: 'zemauth.can_view_actual_costs',
        },
        eYesterdayCost: {
            name: 'Yesterday Spend',
            field: 'e_yesterday_cost',
            checked: false,
            type: 'currency',
            help: 'Amount that you have spent yesterday for promotion on specific ad group.',
            totalRow: true,
            order: true,
            initialOrder: 'desc',
            internal: 'zemauth.can_view_effective_costs',
            shown: 'zemauth.can_view_effective_costs',
        },

        // Media source
        minBidCpc: {
            name: 'Min Bid',
            field: 'min_bid_cpc',
            checked: true,
            type: 'currency',
            shown: true,
            fractionSize: 3,
            help: 'Minimum bid price (in USD) per click.',
            totalRow: false,
            order: true,
            initialOrder: 'desc',
        },
        maxBidCpc: {
            name: 'Max Bid',
            field: 'max_bid_cpc',
            checked: true,
            type: 'currency',
            shown: true,
            fractionSize: 3,
            help: 'Maximum bid price (in USD) per click.',
            totalRow: false,
            order: true,
            initialOrder: 'desc',
        },
        dailyBudget: {
            name: 'Daily Budget',
            field: 'daily_budget',
            checked: true,
            type: 'currency',
            shown: true,
            help: 'Maximum budget per day.',
            totalRow: true,
            order: true,
            initialOrder: 'desc',
        },
        supplyDashUrl: {
            name: 'Link',
            field: 'supply_dash_url',
            checked: false,
            type: 'link',
            totalRow: true,
            order: true,
            initialOrder: 'desc',
            internal: 'zemauth.supply_dash_link_view',
            shown: 'zemauth.supply_dash_link_view',
        },

        // AdGroup Media Sources
        bidCpcSetting: {
            name: 'Bid CPC',
            field: 'bid_cpc',
            checked: true,
            type: 'currency',
            shown: true,
            fractionSize: 3,
            help: 'Maximum bid price (in USD) per click.',
            totalRow: false,
            order: true,
            settingsField: true,
            initialOrder: 'desc',
        },
        currentBidCpc: {
            name: 'Current Bid CPC',
            field: 'current_bid_cpc',
            fractionSize: 3,
            checked: false,
            type: 'currency',
            internal: false,
            shown: false,
            totalRow: false,
            order: true,
            help: 'Cost-per-click (CPC) bid is the approximate amount that you\'ll be charged for a click on your ad.',
            initialOrder: 'desc',
        },
        dailyBudgetSetting: {
            name: 'Daily Budget',
            field: 'daily_budget',
            fractionSize: 0,
            checked: true,
            type: 'currency',
            shown: true,
            help: 'Maximum budget per day.',
            totalRow: true,
            order: true,
            settingsField: true,
            initialOrder: 'desc',
        },
        currentDailyBudget: {
            name: 'Current Daily Budget',
            field: 'current_daily_budget',
            checked: false,
            fractionSize: 0,
            type: 'currency',
            internal: false,
            shown: false,
            totalRow: true,
            order: true,
            help: 'Maximum budget per day.',
            initialOrder: 'desc',
        },

        // Publishers
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
            initialOrder: 'asc',
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
            initialOrder: 'asc',
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
            initialOrder: 'asc',
        },

        // ContentAd fields
        imageUrls: {
            name: 'Thumbnail',
            field: 'image_urls',
            checked: true,
            type: 'image',
            shown: true,
            totalRow: false,
            titleField: 'title',
            order: true,
            orderField: 'image_hash',
            initialOrder: 'asc',
        },
        notification: {
            name: '',
            unselectable: true,
            checked: true,
            type: 'notification',
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
            initialOrder: 'asc',
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
            initialOrder: 'asc',
        },
        uploadTime: {
            name: 'Uploaded',
            field: 'upload_time',
            checked: true,
            type: 'datetime',
            shown: true,
            help: 'The time when the content ad was uploaded.',
            totalRow: false,
            order: true,
            initialOrder: 'desc',
        },
        batchName: {
            name: 'Batch Name',
            field: 'batch_name',
            checked: true,
            type: 'text',
            shown: true,
            help: 'The name of the upload batch.',
            totalRow: false,
            titleField: 'batch_name',
            order: true,
            orderField: 'batch_name',
            initialOrder: 'asc',
        },
        displayUrl: {
            name: 'Display URL',
            field: 'display_url',
            checked: false,
            type: 'text',
            shown: true,
            help: 'Advertiser\'s display URL.',
            totalRow: false,
            titleField: 'display_url',
            order: true,
            orderField: 'display_url',
            initialOrder: 'asc',
        },
        brandName: {
            name: 'Brand Name',
            field: 'brand_name',
            checked: false,
            type: 'text',
            shown: true,
            help: 'Advertiser\'s brand name',
            totalRow: false,
            titleField: 'brand_name',
            order: true,
            orderField: 'brand_name',
            initialOrder: 'asc',
        },
        description: {
            name: 'Description',
            field: 'description',
            checked: false,
            type: 'text',
            shown: true,
            help: 'Description of a content ad.',
            totalRow: false,
            titleField: 'description',
            order: true,
            orderField: 'description',
            initialOrder: 'asc',
        },
        callToAction: {
            name: 'Call to action',
            field: 'call_to_action',
            checked: false,
            type: 'text',
            shown: true,
            help: 'Call to action text.',
            totalRow: false,
            titleField: 'call_to_action',
            order: true,
            orderField: 'call_to_action',
            initialOrder: 'asc',
        },

        // Stats
        mediaCost: {
            name: 'Actual Media Spend',
            field: 'media_cost',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: 'Amount spent per media source, including overspend.',
            order: true,
            initialOrder: 'desc',
            internal: 'zemauth.can_view_actual_costs',
            shown: 'zemauth.can_view_actual_costs',
        },
        eMediaCost: {
            name: 'Media Spend',
            field: 'e_media_cost',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: 'Amount spent per media source.',
            order: true,
            initialOrder: 'desc',
            internal: 'zemauth.can_view_effective_costs',
            shown: 'zemauth.can_view_effective_costs',
        },
        dataCost: {
            name: 'Actual Data Cost',
            field: 'data_cost',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: 'Additional targeting/segmenting costs, including overspend.',
            order: true,
            initialOrder: 'desc',
            internal: 'zemauth.can_view_actual_costs',
            shown: 'zemauth.can_view_actual_costs',
        },
        eDataCost: {
            name: 'Data Cost',
            field: 'e_data_cost',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: 'Additional targeting/segmenting costs.',
            order: true,
            initialOrder: 'desc',
            internal: 'zemauth.can_view_effective_costs',
            shown: 'zemauth.can_view_effective_costs',
        },
        licenseFee: {
            name: 'License Fee',
            field: 'license_fee',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: 'Zemanta One platform usage cost.',
            order: true,
            initialOrder: 'desc',
            internal: 'zemauth.can_view_effective_costs',
            shown: 'zemauth.can_view_effective_costs',
        },
        flatFee: {
            name: 'Recognized Flat Fee',
            field: 'flat_fee',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: '',
            order: true,
            initialOrder: 'desc',
            internal: 'zemauth.can_view_flat_fees',
            shown: 'zemauth.can_view_flat_fees',
        },
        totalFee: {
            name: 'Total Fee',
            field: 'total_fee',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: '',
            order: true,
            initialOrder: 'desc',
            internal: 'zemauth.can_view_flat_fees',
            shown: 'zemauth.can_view_flat_fees',
        },
        billingCost: {
            name: 'Total Spend',
            field: 'billing_cost',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: 'Sum of media spend, data cost and license fee.',
            order: true,
            initialOrder: 'desc',
            internal: 'zemauth.can_view_effective_costs',
            shown: 'zemauth.can_view_effective_costs',
        },
        allocatedBudgets: {
            name: 'Media budgets',
            field: 'allocated_budgets',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: '',
            order: true,
            initialOrder: 'desc',
            internal: 'zemauth.can_see_projections',
            shown: 'zemauth.can_see_projections',
        },
        pacing: {
            name: 'Pacing',
            field: 'pacing',
            checked: false,
            type: 'percent',
            totalRow: true,
            help: '',
            order: true,
            initialOrder: 'desc',
            internal: 'zemauth.can_see_projections',
            shown: 'zemauth.can_see_projections',
        },
        spendProjection: {
            name: 'Spend Projection',
            field: 'spend_projection',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: '',
            order: true,
            initialOrder: 'desc',
            internal: 'zemauth.can_see_projections',
            shown: 'zemauth.can_see_projections',
        },
        licenseFeeProjection: {
            name: 'License Fee Projection',
            field: 'license_fee_projection',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: '',
            order: true,
            initialOrder: 'desc',
            internal: 'zemauth.can_see_projections',
            shown: 'zemauth.can_see_projections',
        },
        totalFeeProjection: {
            name: 'Total Fee Projection',
            field: 'total_fee_projection',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: '',
            order: true,
            initialOrder: 'desc',
            internal: 'zemauth.can_see_projections',
            shown: ['zemauth.can_see_projections', 'zemauth.can_view_flat_fees'],
        },
        cpc: {
            name: 'Avg. CPC',
            field: 'cpc',
            checked: true,
            type: 'currency',
            shown: true,
            fractionSize: 3,
            help: 'The average CPC.',
            totalRow: true,
            order: true,
            initialOrder: 'desc',
        },
        clicks: {
            name: 'Clicks',
            field: 'clicks',
            checked: true,
            type: 'number',
            shown: true,
            help: 'The number of times a content ad has been clicked.',
            totalRow: true,
            order: true,
            initialOrder: 'desc',
        },
        impressions: {
            name: 'Impressions',
            field: 'impressions',
            checked: true,
            type: 'number',
            shown: true,
            totalRow: true,
            help: 'The number of times content ads have been displayed.',
            order: true,
            initialOrder: 'desc',
        },
        ctr: {
            name: 'CTR',
            field: 'ctr',
            checked: true,
            type: 'percent',
            shown: true,
            defaultValue: '0.0%',
            totalRow: true,
            help: 'The number of clicks divided by the number of impressions.',
            order: true,
            initialOrder: 'desc',
        },
    };

    var STATS = [
        COLUMNS.cost,
        COLUMNS.mediaCost,
        COLUMNS.eMediaCost,
        COLUMNS.dataCost,
        COLUMNS.eDataCost,
        COLUMNS.licenseFee,
        COLUMNS.flatFee,
        COLUMNS.totalFee,
        COLUMNS.billingCost,
        COLUMNS.allocatedBudgets,
        COLUMNS.pacing,
        COLUMNS.spendProjection,
        COLUMNS.licenseFeeProjection,
        COLUMNS.totalFeeProjection,
        COLUMNS.cpc,
        COLUMNS.clicks,
        COLUMNS.impressions,
        COLUMNS.ctr,
    ];

    var MEDIA_SOURCE = [
        COLUMNS.mediaSource,
        COLUMNS.performance,
        COLUMNS.statusMediaSource,
        COLUMNS.minBidCpc,
        COLUMNS.maxBidCpc,
        COLUMNS.dailyBudget,
    ].concat(STATS);

    var ALL_ACCOUNTS_ACCOUNTS = [
        COLUMNS.account,
        COLUMNS.agency,
        COLUMNS.statusAccount,
        COLUMNS.defaultAccountManager,
        COLUMNS.defaultSalesRepresentative,
        COLUMNS.accountType,
    ].concat(STATS);

    var ACCOUNT_CAMPAIGNS = [
        COLUMNS.campaign,
        COLUMNS.performance,
        COLUMNS.statusCampaign,
        COLUMNS.campaignManager,
    ].concat(STATS);

    var CAMPAIGN_AD_GROUPS = [
        COLUMNS.adgroup,
        COLUMNS.performance,
        COLUMNS.statusAdGroup,
        COLUMNS.yesterdayCost,
        COLUMNS.actualYesterdayCost,
        COLUMNS.eYesterdayCost,
    ].concat(STATS);

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
    ].concat(STATS);

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
        COLUMNS.actualYesterdayCost,
        COLUMNS.eYesterdayCost,
    ].concat(STATS);

    var AD_GROUP_PUBLISHERS = [
        COLUMNS.statusPublisher,
        COLUMNS.performance,
        COLUMNS.domain,
        COLUMNS.domainLink,
        COLUMNS.exchange,
    ].concat(STATS);


    // //////////////V////////////////////////////////////////////////////////////////////////////////////
    //  COLUMN CATEGORIES
    // //////////////////////////////////////////////////////////////////////////////////////////////////

    var CATEGORIES = [
        {
            name: 'Costs',
            columns: [
                COLUMNS.cost,
                COLUMNS.eDataCost,
                COLUMNS.eMediaCost,
                COLUMNS.mediaCost,
                COLUMNS.eDataCost,
                COLUMNS.dataCost,
                COLUMNS.licenseFee,
                COLUMNS.totalFee,
                COLUMNS.flatFee,
                COLUMNS.billingCost,
                COLUMNS.yesterdayCost,
                COLUMNS.actualYesterdayCost,
                COLUMNS.eYesterdayCost,
            ],
        }, {
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
                COLUMNS.totalFeeProjection,
                COLUMNS.licenseFeeProjection,
                COLUMNS.spendProjection,
                COLUMNS.pacing,
                COLUMNS.allocatedBudgets,
            ],
        },
        {
            name: 'Traffic Acquisition',
            columns: [
                // publisherSelected ??
                COLUMNS.statusPublisher,
                COLUMNS.domain,
                COLUMNS.domainLink,
                COLUMNS.exchange,
                COLUMNS.cost,
                COLUMNS.minBidCpc,
                COLUMNS.maxBidCpc,
                COLUMNS.dailyBudget,
                COLUMNS.dailyBudgetSetting,
                COLUMNS.clicks,
                COLUMNS.cpc,
            ],
        },
        {
            name: 'Audience Metrics',
            columns: [ // FIXME: goal metrics
                // visits
                // pageviews
                // percent_new_users
                // bounce_rate
                // pv_per_visit
                // avg_tos
                // click_discrepancy
            ],
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
            columns: [ // FIXME: conversion goals
                // conversion_goal_1
                // conversion_goal_2
                // conversion_goal_3
                // conversion_goal_4
                // conversion_goal_5
            ],
        },
        // TODO: zemOptimisationMetricsService.createColumnCategories(),
    ];

    // //////////////V////////////////////////////////////////////////////////////////////////////////////
    // Service stuff
    // //////////////////////////////////////////////////////////////////////////////////////////////////

    function convertPermission (permission, checkFn) {
        // Convert Column definitions permissions to boolean value using passed function
        // 3 versions are possible: boolean, string, array
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
        // TODO: use constants
        var columns;
        if (breakdown === 'source') {
            switch (level) {
            case 'ad_groups': columns = AD_GROUP_MEDIA_SOURCE; break;
            default: columns = MEDIA_SOURCE; break;
            }
        } else if (breakdown === 'publisher') {
            switch (level) {
            case 'ad_groups': columns = AD_GROUP_PUBLISHERS; break;
            default: throw 'Not supported.';
            }
        } else {
            switch (level) {
            case 'all_accounts': columns = ALL_ACCOUNTS_ACCOUNTS; break;
            case 'accounts': columns = ACCOUNT_CAMPAIGNS; break;
            case 'campaigns': columns = CAMPAIGN_AD_GROUPS; break;
            case 'ad_groups': columns = AD_GROUP_CONTENT_ADS; break;
            default: throw 'Not supported.';
            }
        }

        return columns;
    }

    function createColumns ($scope, level, breakdown) {
        // Create columns definitions array based on base level and breakdown
        var columns = getColumns(level, breakdown);
        columns = angular.copy(columns);
        checkPermissions($scope, columns);
        return columns;
    }

    function createCategories (columns) {
        // Create categories in correct format
        // TODO: check if column is required in category
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

    return {
        createColumns: createColumns,
        createCategories: createCategories,
    };
}]);
