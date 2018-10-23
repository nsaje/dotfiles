angular.module('one.widgets').component('zemAdGroupGeneralSettings', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    template: require('./zemAdGroupGeneralSettings.component.html'),
    controller: function(
        $scope,
        $state,
        zemPermissions,
        zemNavigationNewService,
        zemMulticurrencyService
    ) {
        var $ctrl = this;
        $ctrl.options = options;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.MESSAGES = {
            WARNING_END_DATE:
                'Your campaign has been switched to landing mode. ' +
                'Please add the budget and continue to adjust settings by your needs. ',
            WARNING_MAX_CPM: '',
            INFO_CLICK_CAPPING:
                'Outbrain and Yahoo don’t support click capping and will be automatically paused in this ad group if you enable this setting.',
            WARNING_CAMPAIGN_BUDGET_OPTIMIZATION_FLIGHT_TIME:
                'Flight time settings are disabled because campaign budget ' +
                'optimization is enabled. Budget flight time is used for ' +
                'running the ad group.',
        };
        $ctrl.deliveryType = {
            STANDARD: 1,
            ACCELERATED: 2,
        };
        $ctrl.biddingType = constants.biddingType;

        $ctrl.startDatePicker = {isOpen: false};
        $ctrl.endDatePicker = {isOpen: false};
        $ctrl.endDatePickerOptions = {minDate: new Date()};
        $ctrl.openDatePicker = openDatePicker;
        $ctrl.goToBudgets = goToBudgets;
        $ctrl.setBidSectionVisibility = setBidSectionVisibility;

        $ctrl.isBidCpcSectionVisible = false;
        $ctrl.isBidCpmSectionVisible = false;

        $ctrl.$onInit = function() {
            initializeWatches();
            $ctrl.api.register({
                // Not needed (placeholder)
            });

            $ctrl.currencySymbol = zemMulticurrencyService.getAppropriateCurrencySymbol(
                zemNavigationNewService.getActiveAccount()
            );
        };

        $ctrl.$onChanges = function() {
            if ($ctrl.entity && $ctrl.entity.warnings.maxCpm) {
                $ctrl.MESSAGES.WARNING_MAX_CPM =
                    'You have some active media sources ' +
                    "that don't support max CPM restriction. To start using it, please " +
                    'disable/pause these media sources: ' +
                    $ctrl.entity.warnings.maxCpm.sources.join(', ') +
                    '.';
            }

            if ($ctrl.entity && $ctrl.entity.settings) {
                setBidSectionVisibility($ctrl.entity.settings.biddingType);
            }
        };

        function goToBudgets() {
            var campaignId = zemNavigationNewService.getActiveEntity().parent
                .id;
            $state.go('v2.analytics', {
                id: campaignId,
                level: 'campaign',
                settings: true,
                settingsScrollTo: 'zemCampaignBudgetsSettings',
            });
        }

        function initializeWatches() {
            // TODO: Refactor - remove the need for watches
            $scope.$watch('$ctrl.entity.settings.manualStop', function(
                newValue
            ) {
                if (!$ctrl.entity) return;
                if (newValue) {
                    $ctrl.entity.settings.endDate = null;
                }
            });

            $scope.$watch('$ctrl.entity.settings.endDate', function(newValue) {
                if (!$ctrl.entity) return;
                if (newValue) {
                    $ctrl.entity.settings.manualStop = false;
                } else {
                    $ctrl.entity.settings.manualStop = true;
                }
            });
        }

        function setBidSectionVisibility(biddingType) {
            if (
                biddingType === constants.biddingType.CPC &&
                zemPermissions.hasPermission('zemauth.can_set_ad_group_max_cpc')
            ) {
                $ctrl.isBidCpcSectionVisible = true;
                $ctrl.isBidCpmSectionVisible = false;
            }

            if (
                biddingType === constants.biddingType.CPM &&
                zemPermissions.hasPermission('zemauth.fea_can_use_cpm_buying')
            ) {
                $ctrl.isBidCpcSectionVisible = false;
                $ctrl.isBidCpmSectionVisible = true;
            }
        }

        function openDatePicker(type) {
            if (type === 'startDate') {
                $ctrl.startDatePicker.isOpen = true;
            } else if (type === 'endDate') {
                $ctrl.endDatePicker.isOpen = true;
            }
        }
    },
});
