angular.module('one.widgets').component('zemGridContainerActions', {
    template: require('./zemGridContainerActions.component.html'),
    bindings: {
        entity: '<',
        breakdown: '<',
        level: '<',
        gridApi: '<',
    },
    controller: function(
        $scope,
        zemPermissions,
        zemNavigationNewService,
        zemGridActionsService,
        zemGridConstants
    ) {
        var $ctrl = this;
        $ctrl.constants = constants;
        $ctrl.selectedRows = [];
        $ctrl.level = undefined;
        $ctrl.accountId = undefined;
        $ctrl.campaignId = undefined;
        $ctrl.adGroupId = undefined;

        $ctrl.isEntityBreakdown = isEntityBreakdown;
        $ctrl.isGridExportVisible = isGridExportVisible;
        $ctrl.isGridBulkActionsVisible = isGridBulkActionsVisible;
        $ctrl.isGridBulkBlacklistActionsVisible = isGridBulkBlacklistActionsVisible;
        $ctrl.isCreateEntityActionVisible = isCreateEntityActionVisible;
        $ctrl.isCreateAdGroupSourceActionVisible = isCreateAdGroupSourceActionVisible;
        $ctrl.isReportDropdownVisible = isReportDropdownVisible;
        $ctrl.canCreateNewAccount = canCreateNewAccount;
        $ctrl.isBreakdownSelectorVisible = isBreakdownSelectorVisible;
        $ctrl.areBidModifierActionsVisible = areBidModifierActionsVisible;
        $ctrl.areRuleActionsVisible = areRuleActionsVisible;

        $ctrl.$onInit = function() {
            $ctrl.level = $ctrl.gridApi.getMetaData().level;
            $ctrl.entity = zemNavigationNewService.getActiveEntity();

            var account = zemNavigationNewService.getActiveEntityByType(
                constants.entityType.ACCOUNT
            );
            var campaign = zemNavigationNewService.getActiveEntityByType(
                constants.entityType.CAMPAIGN
            );
            var adGroup = zemNavigationNewService.getActiveEntityByType(
                constants.entityType.AD_GROUP
            );

            $ctrl.accountId = account ? account.id : undefined;
            $ctrl.campaignId = campaign ? campaign.id : undefined;
            $ctrl.adGroupId = adGroup ? adGroup.id : undefined;
            $ctrl.gridApi.onSelectionUpdated($scope, updateSelectedRowsList);
        };

        function updateSelectedRowsList() {
            if (
                $ctrl.gridApi.getSelection().type ===
                zemGridConstants.gridSelectionFilterType.ALL
            ) {
                $ctrl.selectedRows = [];
            } else {
                $ctrl.selectedRows = $ctrl.gridApi
                    .getSelection()
                    .selected.map(function(row) {
                        return zemGridActionsService.mapRowForBlacklisting(
                            row,
                            $ctrl.breakdown
                        );
                    })
                    .filter(function(row) {
                        return row.source !== undefined;
                    });
            }
        }

        function isEntityBreakdown() {
            return (
                $ctrl.breakdown !== constants.breakdown.MEDIA_SOURCE &&
                $ctrl.breakdown !== constants.breakdown.PUBLISHER &&
                $ctrl.breakdown !== constants.breakdown.PLACEMENT &&
                $ctrl.breakdown !== constants.breakdown.COUNTRY &&
                $ctrl.breakdown !== constants.breakdown.STATE &&
                $ctrl.breakdown !== constants.breakdown.DMA &&
                $ctrl.breakdown !== constants.breakdown.DEVICE &&
                $ctrl.breakdown !== constants.breakdown.ENVIRONMENT &&
                $ctrl.breakdown !== constants.breakdown.OPERATING_SYSTEM
            );
        }

        function canCreateNewAccount() {
            return (
                zemPermissions.hasPermission(
                    'zemauth.all_accounts_accounts_add_account'
                ) || $ctrl.level !== constants.level.ALL_ACCOUNTS
            );
        }

        function isGridBulkActionsVisible() {
            return (
                isEntityBreakdown() ||
                ($ctrl.breakdown === constants.breakdown.MEDIA_SOURCE &&
                    $ctrl.entity &&
                    $ctrl.entity.type === constants.entityType.AD_GROUP)
            );
        }

        function isGridBulkBlacklistActionsVisible() {
            return (
                $ctrl.breakdown === constants.breakdown.PUBLISHER ||
                $ctrl.breakdown === constants.breakdown.PLACEMENT
            );
        }

        function isCreateEntityActionVisible() {
            return isEntityBreakdown();
        }

        function isCreateAdGroupSourceActionVisible() {
            if (zemPermissions.hasPermission('zemauth.disable_public_rcs')) {
                return false;
            }
            return (
                $ctrl.breakdown === constants.breakdown.MEDIA_SOURCE &&
                $ctrl.entity &&
                $ctrl.entity.type === constants.entityType.AD_GROUP
            );
        }

        function isGridExportVisible() {
            return (
                $ctrl.breakdown !== constants.breakdown.PUBLISHER &&
                !zemPermissions.hasPermission(
                    'zemauth.can_see_new_report_schedule'
                )
            );
        }

        function isReportDropdownVisible() {
            return (
                ($ctrl.breakdown === constants.breakdown.PUBLISHER &&
                    zemPermissions.hasPermission(
                        'zemauth.can_access_publisher_reports'
                    )) ||
                ($ctrl.breakdown !== constants.breakdown.PUBLISHER &&
                    zemPermissions.hasPermission(
                        'zemauth.can_see_new_report_schedule'
                    ))
            );
        }

        function isBreakdownSelectorVisible() {
            return (
                $ctrl.breakdown !== constants.breakdown.PLACEMENT &&
                $ctrl.breakdown !== constants.breakdown.COUNTRY &&
                $ctrl.breakdown !== constants.breakdown.STATE &&
                $ctrl.breakdown !== constants.breakdown.DMA &&
                $ctrl.breakdown !== constants.breakdown.DEVICE &&
                $ctrl.breakdown !== constants.breakdown.ENVIRONMENT &&
                $ctrl.breakdown !== constants.breakdown.OPERATING_SYSTEM
            );
        }

        function areBidModifierActionsVisible() {
            return (
                $ctrl.entity &&
                $ctrl.entity.type === constants.entityType.AD_GROUP &&
                (areDeliveryBidModifierActionsVisible() ||
                    areSourceBidModifierActionsVisible() ||
                    arePublisherBidModifierActionsVisible())
            );
        }

        function arePublisherBidModifierActionsVisible() {
            return (
                zemPermissions.hasPermission(
                    'zemauth.can_use_publisher_bid_modifiers_in_ui'
                ) && $ctrl.breakdown === constants.breakdown.PUBLISHER
            );
        }

        function areDeliveryBidModifierActionsVisible() {
            return (
                zemPermissions.hasPermission('zemauth.can_set_bid_modifiers') &&
                ($ctrl.breakdown === constants.breakdown.CONTENT_AD ||
                    $ctrl.breakdown === constants.breakdown.COUNTRY ||
                    $ctrl.breakdown === constants.breakdown.STATE ||
                    $ctrl.breakdown === constants.breakdown.DMA ||
                    $ctrl.breakdown === constants.breakdown.DEVICE ||
                    $ctrl.breakdown === constants.breakdown.ENVIRONMENT ||
                    $ctrl.breakdown === constants.breakdown.OPERATING_SYSTEM)
            );
        }

        function areSourceBidModifierActionsVisible() {
            return (
                zemPermissions.hasPermission(
                    'zemauth.can_set_source_bid_modifiers'
                ) && $ctrl.breakdown === constants.breakdown.MEDIA_SOURCE
            );
        }

        function areRuleActionsVisible() {
            return (
                $ctrl.entity &&
                zemPermissions.hasPermission(
                    'zemauth.fea_can_create_automation_rules'
                ) &&
                ($ctrl.entity.type === constants.entityType.AD_GROUP ||
                    $ctrl.entity.type === constants.entityType.CAMPAIGN)
            );
        }
    },
});
