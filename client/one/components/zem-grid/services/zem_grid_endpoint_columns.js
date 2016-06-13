/* globals oneApp, angular */
'use strict';

oneApp.factory('zemGridEndpointColumns', ['$rootScope', '$controller', '$http', '$q', function ($rootScope, $controller, $http, $q) { // eslint-disable-line max-len

    // //////////////////////////////////////////////////////////////////////////////////////////////////
    //  COLUMNS
    // //////////////////////////////////////////////////////////////////////////////////////////////////

    // FIXME: permissions
    // FIXME: status, state refactoring
    // FIXME: help content
    // TODO: split COLUMNS - stats, object, status, etc.
    // TODO: categories
    // TODO: conversion goals
    // TODO: default values : unselectable, checked, shown, totalRow, order, orderField==field, initialOrder
    

    var COLUMNS = {
        account: {
            name: 'Account',
            field: 'name_link',
            unselectable: true,
            checked: true,
            type: 'linkNav',
            shown: true,
            hasTotalsLabel: true, // FIXME: is it needed?
            totalRow: false,
            help: 'A partner account.',
            order: true,
            orderField: 'name',
            initialOrder: 'asc'
        },
        campaign: {
            name: 'Campaign',
            field: 'name',
            unselectable: true,
            checked: true,
            type: 'linkNav',
            shown: true,
            hasTotalsLabel: true,
            totalRow: false,
            help: 'Name of the campaign.',
            order: true,
            initialOrder: 'asc'
        },
        adgroup: {
            name: 'Ad Group',
            field: 'name',
            unselectable: true,
            checked: true,
            type: 'linkNav',
            shown: true,
            hasTotalsLabel: true,
            totalRow: false,
            help: 'Name of the ad group.',
            order: true,
            initialOrder: 'asc'
        },
        mediaSource: {
            name: 'Media Source',
            field: 'name',
            unselectable: true,
            checked: true,
            type: 'clickPermissionOrText',
            hasPermission: $scope.hasPermission('zemauth.can_filter_sources_through_table'),
            clickCallback: zemFilterService.exclusivelyFilterSource,
            shown: true,
            hasTotalsLabel: true,
            totalRow: false,
            help: 'A media source where your content is being promoted.',
            order: true,
            initialOrder: 'asc'
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
            internal: $scope.isPermissionInternal('zemauth.can_view_account_agency_information'),
            shown: $scope.hasPermission('zemauth.can_view_account_agency_information')
        },
        accountManager: {
            name: 'Account Manager',
            field: 'default_account_manager',
            checked: false,
            type: 'text',
            totalRow: false,
            help: 'Account manager responsible for the campaign and the communication with the client.',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_see_managers_in_accounts_table'),
            shown: $scope.hasPermission('zemauth.can_see_managers_in_accounts_table')
        },
        salesRepresentative: {
            name: 'Sales Representative',
            field: 'default_sales_representative',
            checked: false,
            type: 'text',
            totalRow: false,
            help: 'Sales representative responsible for the campaign and the communication with the client.',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_see_managers_in_accounts_table'),
            shown: $scope.hasPermission('zemauth.can_see_managers_in_accounts_table')
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
            internal: $scope.isPermissionInternal('zemauth.can_see_managers_in_campaigns_table'),
            shown: $scope.hasPermission('zemauth.can_see_managers_in_campaigns_table'),
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
            internal: $scope.isPermissionInternal('zemauth.can_see_account_type'),
            shown: $scope.hasPermission('zemauth.can_see_account_type')
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
            internal: $scope.isPermissionInternal('zemauth.campaign_goal_performance'),
            shown: $scope.hasPermission('zemauth.campaign_goal_performance')
        },

        // Status TODO: refactor
        statusAccount: {
            name: 'Status',
            field: 'status',
            unselectable: true,
            checked: true,
            type: 'text',
            shown: true,
            totalRow: false,
            help: 'Status of an account (enabled or paused). An account is paused only if all its campaigns are paused too; otherwise the account is enabled.',
            order: true,
            orderField: 'status',
            initialOrder: 'asc'
        },
        statusCampaign: {
            name: 'Status',
            field: 'state',
            checked: true,
            type: 'text',
            shown: true,
            totalRow: false,
            help: 'Status of a campaign (enabled or paused). A campaign is paused only if all its ad groups are paused too; otherwise, the campaign is enabled.',
            order: true,
            initialOrder: 'asc'
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
            initialOrder: 'asc'
        },
        statusContentAd: {
            name: '\u25CF',
            field: 'status_setting',
            type: 'state',
            order: true,
            initialOrder: 'asc',
            enabledValue: constants.contentAdSourceState.ACTIVE,
            pausedValue: constants.contentAdSourceState.INACTIVE,
            internal: false,
            shown: true,
            checked: true,
            totalRow: false,
            unselectable: true,
            help: 'A setting for enabling and pausing content ads.',
            onChange: function (contentAdId, state) {
                api.adGroupContentAdState.save($state.params.id, state, [contentAdId]).then(
                    function () {
                        $scope.pollTableUpdates();
                    }
                );
            },
            getDisabledMessage: function (row) {
                return 'This ad must be managed manually.';
            },
            disabled: false,
            archivedField: 'archived'
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
            initialOrder: 'asc'
        },

        // State TODO: refactor
        stateAdGroup: { // AdGroup state
            name: '\u25CF',
            field: 'state',
            type: 'state',
            order: true,
            editable: true,
            initialOrder: 'asc',
            enabledValue: constants.adGroupSourceSettingsState.ACTIVE,
            pausedValue: constants.adGroupSourceSettingsState.INACTIVE,
            internal: $scope.isPermissionInternal('zemauth.can_control_ad_group_state_in_table'),
            shown: $scope.hasPermission('zemauth.can_control_ad_group_state_in_table'),
            checked: true,
            totalRow: false,
            unselectable: true,
            help: 'A setting for enabling and pausing Ad Groups.',
            onChange: function (adgroupId, state) {
                $scope.rows.forEach(function (row) {
                    if (row.id === adgroupId) {
                        row.stateText = $scope.getStateText(state);
                    }
                });
                zemNavigationService.notifyAdGroupReloading(adgroupId, true);

                api.adGroupSettingsState.post(adgroupId, state).then(
                    function (data) {
                        // reload ad group to update its status
                        zemNavigationService.reloadAdGroup(adgroupId);
                    },
                    function () {
                        zemNavigationService.notifyAdGroupReloading(adgroupId, false);
                    }
                );
            },
            getDisabledMessage: function (row) {
                return row.editable_fields.state.message;
            },
            disabled: false,
            archivedField: 'archived'
        },
        stateContentAd: {
            name: '\u25CF',
            field: 'status_setting',
            type: 'state',
            order: true,
            initialOrder: 'asc',
            enabledValue: constants.contentAdSourceState.ACTIVE,
            pausedValue: constants.contentAdSourceState.INACTIVE,
            internal: false,
            shown: true,
            checked: true,
            totalRow: false,
            unselectable: true,
            help: 'A setting for enabling and pausing content ads.',
            onChange: function (contentAdId, state) {
                api.adGroupContentAdState.save($state.params.id, state, [contentAdId]).then(
                    function () {
                        $scope.pollTableUpdates();
                    }
                );
            },
            getDisabledMessage: function (row) {
                return 'This ad must be managed manually.';
            },
            disabled: false,
            archivedField: 'archived'
        },

        // Media source
        minCpc: {
            name: 'Min Bid',
            field: 'min_bid_cpc',
            checked: true,
            type: 'currency',
            shown: true,
            fractionSize: 3,
            help: 'Minimum bid price (in USD) per click.',
            totalRow: false,
            order: true,
            initialOrder: 'desc'
        },
        maxCpc: {
            name: 'Max Bid',
            field: 'max_bid_cpc',
            checked: true,
            type: 'currency',
            shown: true,
            fractionSize: 3,
            help: 'Maximum bid price (in USD) per click.',
            totalRow: false,
            order: true,
            initialOrder: 'desc'
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
            initialOrder: 'desc'
        },

        // ContentAd fields
        thumbnail: {
            name: 'Thumbnail',
            field: 'image_urls',
            checked: true,
            type: 'image',
            shown: true,
            totalRow: false,
            titleField: 'title',
            order: true,
            orderField: 'image_hash',
            initialOrder: 'asc'
        },
        submissionStatus: {
            name: 'Status',
            field: 'submission_status',
            checked: false,
            type: 'submissionStatus',
            archivedField: 'archived',
            shown: true,
            help: 'Current submission status.',
            totalRow: false,
        },
        notification: { // FIXME: ?
            name: '',
            unselectable: true,
            checked: true,
            type: 'notification',
            shown: true,
            totalRow: false,
            extraTdCss: 'notification-no-text'
        },
        title: {
            name: 'Title',
            field: 'titleLink',
            checked: true,
            type: 'linkText',
            shown: true,
            totalRow: false,
            help: 'The creative title/headline of a content ad. The link to landing page includes tracking codes.',
            extraTdCss: 'trimmed title',
            titleField: 'title',
            order: true,
            orderField: 'title',
            initialOrder: 'asc'
        },
        url: {
            name: 'URL',
            field: 'urlLink',
            checked: true,
            type: 'linkText',
            shown: true,
            help: 'The web address of the content ad.',
            extraTdCss: 'trimmed url',
            totalRow: false,
            titleField: 'url',
            order: true,
            orderField: 'url',
            initialOrder: 'asc'
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
            initialOrder: 'desc'
        },
        batchName: {
            name: 'Batch Name',
            field: 'batch_name',
            checked: true,
            extraTdCss: 'no-wrap',
            type: 'text',
            shown: true,
            help: 'The name of the upload batch.',
            totalRow: false,
            titleField: 'batch_name',
            order: true,
            orderField: 'batch_name',
            initialOrder: 'asc'
        },
        displayUrl: {
            name: 'Display URL',
            field: 'display_url',
            checked: false,
            extraTdCss: 'no-wrap',
            type: 'text',
            shown: true,
            help: 'Advertiser\'s display URL.',
            totalRow: false,
            titleField: 'display_url',
            order: true,
            orderField: 'display_url',
            initialOrder: 'asc'
        },
        brandName: {
            name: 'Brand Name',
            field: 'brand_name',
            checked: false,
            extraTdCss: 'no-wrap',
            type: 'text',
            shown: true,
            help: 'Advertiser\'s brand name',
            totalRow: false,
            titleField: 'brand_name',
            order: true,
            orderField: 'brand_name',
            initialOrder: 'asc'
        },
        description: {
            name: 'Description',
            field: 'description',
            checked: false,
            extraTdCss: 'no-wrap',
            type: 'text',
            shown: true,
            help: 'Description of a content ad.',
            totalRow: false,
            titleField: 'description',
            order: true,
            orderField: 'description',
            initialOrder: 'asc'
        },
        callToAction: {
            name: 'Call to action',
            field: 'call_to_action',
            checked: false,
            extraTdCss: 'no-wrap',
            type: 'text',
            shown: true,
            help: 'Call to action text.',
            totalRow: false,
            titleField: 'call_to_action',
            order: true,
            orderField: 'call_to_action',
            initialOrder: 'asc'
        },

        // Stats
        spend: {
            name: 'Spend',
            field: 'cost',
            checked: true,
            type: 'currency',
            help: 'Amount spent per account', 
            totalRow: true,
            order: true,
            initialOrder: 'desc',
            shown: !$scope.hasPermission('zemauth.can_view_effective_costs') && !$scope.hasPermission('zemauth.can_view_actual_costs')
        },
        actualMediaSpend: {
            name: 'Actual Media Spend',
            field: 'media_cost',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: 'Amount spent per media source, including overspend.',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_view_actual_costs'),
            shown: $scope.hasPermission('zemauth.can_view_actual_costs')
        },
        mediaSpend: {
            name: 'Media Spend',
            field: 'e_media_cost',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: 'Amount spent per media source.',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_view_effective_costs'),
            shown: $scope.hasPermission('zemauth.can_view_effective_costs')
        },
        actualDataCost: {
            name: 'Actual Data Cost',
            field: 'data_cost',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: 'Additional targeting/segmenting costs, including overspend.',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_view_actual_costs'),
            shown: $scope.hasPermission('zemauth.can_view_actual_costs')
        },
        dataCost: {
            name: 'Data Cost',
            field: 'e_data_cost',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: 'Additional targeting/segmenting costs.',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_view_effective_costs'),
            shown: $scope.hasPermission('zemauth.can_view_effective_costs')
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
            internal: $scope.isPermissionInternal('zemauth.can_view_effective_costs'),
            shown: $scope.hasPermission('zemauth.can_view_effective_costs')
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
            internal: $scope.isPermissionInternal('zemauth.can_view_flat_fees'),
            shown: $scope.hasPermission('zemauth.can_view_flat_fees')
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
            internal: $scope.isPermissionInternal('zemauth.can_view_flat_fees'),
            shown: $scope.hasPermission('zemauth.can_view_flat_fees')
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
            internal: $scope.isPermissionInternal('zemauth.can_view_effective_costs'),
            shown: $scope.hasPermission('zemauth.can_view_effective_costs')
        },
        mediaBudgets: {
            name: 'Media budgets',
            field: 'allocated_budgets',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: '',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_see_projections'),
            shown: $scope.hasPermission('zemauth.can_see_projections')
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
            internal: $scope.isPermissionInternal('zemauth.can_see_projections'),
            shown: $scope.hasPermission('zemauth.can_see_projections')
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
            internal: $scope.isPermissionInternal('zemauth.can_see_projections'),
            shown: $scope.hasPermission('zemauth.can_see_projections')
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
            internal: $scope.isPermissionInternal('zemauth.can_see_projections'),
            shown: $scope.hasPermission('zemauth.can_see_projections')
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
            internal: $scope.isPermissionInternal('zemauth.can_see_projections'),
            shown: $scope.hasPermission('zemauth.can_see_projections') && $scope.hasPermission('zemauth.can_view_flat_fees')
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
            initialOrder: 'desc'
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
            initialOrder: 'desc'
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
            initialOrder: 'desc'
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
            initialOrder: 'desc'
        },

        // data status
        dataStaus: {
            name: '',
            nameCssClass: 'data-status-icon',
            type: 'dataStatus',
            internal: $scope.isPermissionInternal('zemauth.data_status_column'),
            shown: false,
            checked: true,
            totalRow: false,
            unselectable: true,
            help: 'Status of third party data accuracy.',
            disabled: false
        },
        lastSync: {
            name: 'Last OK Sync (EST)',
            field: 'last_sync',
            checked: false,
            type: 'datetime',
            shown: false,
            help: 'Dashboard reporting data is synchronized on an hourly basis. This is when the most recent synchronization occurred (in Eastern Standard Time).',
            order: true,
            initialOrder: 'desc'
        }
    };

    // //////////////////////////////////////////////////////////////////////////////////////////////////
    //  COLUMN CATEGORIES
    // //////////////////////////////////////////////////////////////////////////////////////////////////

    return {
        createMetaData: createMetaData,
    };
}]);
