var arrayHelpers = require('../../../../../shared/helpers/array.helpers');

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
        zemAuthStore,
        zemNavigationNewService,
        zemGridActionsService,
        zemGridConstants
    ) {
        var $ctrl = this;
        $ctrl.constants = constants;
        $ctrl.selectedRows = [];
        $ctrl.publisherInfoRows = [];
        $ctrl.level = undefined;
        $ctrl.agencyId = undefined;
        $ctrl.accountId = undefined;
        $ctrl.campaignId = undefined;
        $ctrl.adGroupId = undefined;

        $ctrl.isEntityBreakdown = isEntityBreakdown;
        $ctrl.isGridExportVisible = isGridExportVisible;
        $ctrl.isGridBulkActionsVisible = isGridBulkActionsVisible;
        $ctrl.areGridPublisherAndPlacementActionsVisible = areGridPublisherAndPlacementActionsVisible;
        $ctrl.isAddToPublishersAndPlacementsButtonVisible = isAddToPublishersAndPlacementsButtonVisible;
        $ctrl.isCreateEntityActionVisible = isCreateEntityActionVisible;
        $ctrl.isCreateAdGroupSourceActionVisible = isCreateAdGroupSourceActionVisible;
        $ctrl.isReportDropdownVisible = isReportDropdownVisible;
        $ctrl.isCreateEntityActionDisabled = isCreateEntityActionDisabled;
        $ctrl.isBreakdownSelectorVisible = isBreakdownSelectorVisible;
        $ctrl.areBidModifierActionsVisible = areBidModifierActionsVisible;
        $ctrl.areRuleActionsVisible = areRuleActionsVisible;
        $ctrl.hasReadOnlyAccess = hasReadOnlyAccess;

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

            $ctrl.agencyId = account
                ? (account.data || {}).agencyId
                : undefined;
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
                    .selected.filter(function(row) {
                        return row.level === 1;
                    });
            }
            $ctrl.publisherInfoRows = getPublisherInfoRows(
                $ctrl.selectedRows,
                $ctrl.breakdown
            );
        }

        function getPublisherInfoRows(selectedRows, breakdown) {
            if (arrayHelpers.isEmpty(selectedRows)) {
                return [];
            }
            return selectedRows
                .map(function(row) {
                    return zemGridActionsService.mapRowToPublisherInfo(
                        row,
                        breakdown
                    );
                })
                .filter(function(row) {
                    return row !== undefined && row.sourceId !== undefined;
                });
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

        function isCreateEntityActionDisabled() {
            if ($ctrl.level === constants.level.ALL_ACCOUNTS) {
                return !zemAuthStore.canCreateNewAccount();
            }
            return zemAuthStore.hasReadOnlyAccessOn(
                $ctrl.agencyId,
                $ctrl.accountId
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

        function areGridPublisherAndPlacementActionsVisible() {
            return (
                $ctrl.level !== constants.level.ALL_ACCOUNTS &&
                ($ctrl.breakdown === constants.breakdown.PUBLISHER ||
                    $ctrl.breakdown === constants.breakdown.PLACEMENT)
            );
        }

        function isAddToPublishersAndPlacementsButtonVisible() {
            return (
                areGridPublisherAndPlacementActionsVisible() &&
                zemAuthStore.hasPermission(
                    'zemauth.can_see_add_to_pub_plac_button'
                )
            );
        }

        function isCreateEntityActionVisible() {
            return isEntityBreakdown();
        }

        function isCreateAdGroupSourceActionVisible() {
            if (zemAuthStore.hasPermission('zemauth.disable_public_rcs')) {
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
                !zemAuthStore.hasPermission(
                    'zemauth.can_see_new_report_schedule'
                )
            );
        }

        function isReportDropdownVisible() {
            return (
                ($ctrl.breakdown === constants.breakdown.PUBLISHER &&
                    zemAuthStore.hasPermission(
                        'zemauth.can_access_publisher_reports'
                    )) ||
                ($ctrl.breakdown !== constants.breakdown.PUBLISHER &&
                    zemAuthStore.hasPermission(
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
                    arePublisherAndPlacementBidModifierActionsVisible())
            );
        }

        function arePublisherAndPlacementBidModifierActionsVisible() {
            return (
                $ctrl.breakdown === constants.breakdown.PUBLISHER ||
                $ctrl.breakdown === constants.breakdown.PLACEMENT
            );
        }

        function areDeliveryBidModifierActionsVisible() {
            return (
                zemAuthStore.hasPermission('zemauth.can_set_bid_modifiers') &&
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
                zemAuthStore.hasPermission(
                    'zemauth.can_set_source_bid_modifiers'
                ) && $ctrl.breakdown === constants.breakdown.MEDIA_SOURCE
            );
        }

        function areRuleActionsVisible() {
            return (
                $ctrl.entity &&
                zemAuthStore.hasPermission(
                    'zemauth.fea_can_create_automation_rules'
                ) &&
                ($ctrl.entity.type === constants.entityType.ACCOUNT ||
                    $ctrl.entity.type === constants.entityType.CAMPAIGN ||
                    $ctrl.entity.type === constants.entityType.AD_GROUP)
            );
        }

        function hasReadOnlyAccess() {
            return zemAuthStore.hasReadOnlyAccessOn(
                $ctrl.agencyId,
                $ctrl.accountId
            );
        }
    },
});
