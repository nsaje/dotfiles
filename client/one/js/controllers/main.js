/* globals $, angular, constants */
angular.module('one.legacy').controller('MainCtrl', function ($scope, $state, $location, $document, $q, $uibModal, $uibModalStack, $timeout, $window, zemMoment, zemUserService, zemPermissions, api, zemFullStoryService, zemNavigationService, accountsAccess, zemHeaderDateRangePickerService, zemDataFilterService) { // eslint-disable-line max-len
    $scope.accountsAccess = accountsAccess;
    $scope.accounts = [];

    $scope.user = zemUserService.current();
    $scope.currentRoute = $scope.current;
    $scope.inputDateFormat = 'M/D/YYYY';
    $scope.enablePublisherFilter = false;
    $scope.showSelectedPublisher = null;
    $scope.localStoragePrefix = 'main';

    $scope.adGroupData = {};
    $scope.account = null;
    $scope.campaign = null;
    $scope.adGroup = null;

    $scope.hasPermission = zemPermissions.hasPermission;
    $scope.isPermissionInternal = zemPermissions.isPermissionInternal;

    $scope.allowLivestream = zemFullStoryService.allowLivestream;
    $scope.liveStreamOn = zemFullStoryService.isLivestreamAllowed;

    $scope.hasAgency = function () {
        if ($scope.user.agency) {
            return true;
        }
        return false;
    };

    $scope.reflowGraph = function (delay) {
        $timeout(function () {
            $window.dispatchEvent(new Event('resize'));
            $scope.$broadcast('highchartsng.reflow');
        }, delay);
    };

    $scope.getDefaultAllAccountsState = function () {
        // keep the same tab if possible
        if ($state.includes('**.sources') && $scope.hasPermission('zemauth.all_accounts_sources_view')) {
            return 'main.allAccounts.sources';
        }

        // otherwise get default state
        if ($scope.hasPermission('zemauth.all_accounts_accounts_view')) {
            return 'main.allAccounts.accounts';
        }
        if ($scope.hasPermission('zemauth.all_accounts_sources_view')) {
            return 'main.allAccounts.sources';
        }

        // no permissions
        return null;
    };

    $scope.canAccessAllAccounts = function () {
        return !!$scope.getDefaultAllAccountsState();
    };

    $scope.getDefaultAccountState = function () {
        // keep the same tab if possible
        if ($state.includes('**.sources') && $scope.hasPermission('zemauth.account_sources_view')) {
            return 'main.accounts.sources';
        }
        if ($state.includes('**.history') && $scope.hasPermission('zemauth.account_history_view')) {
            return 'main.accounts.history';
        }
        if ($state.includes('**.settings') && $scope.hasPermission('zemauth.account_account_view')) {
            return 'main.accounts.settings';
        }
        if ($scope.hasPermission('zemauth.account_credit_view') && ($state.includes('**.budget') || $state.includes('**.credit'))) {
            return 'main.accounts.credit';
        }

        // otherwise get default state
        if ($scope.hasPermission('zemauth.account_campaigns_view')) {
            return 'main.accounts.campaigns';
        }
        if ($scope.hasPermission('zemauth.account_sources_view')) {
            return 'main.accounts.sources';
        }
        if ($scope.hasPermission('zemauth.account_account_view')) {
            return 'main.accounts.settings';
        }

        // no permissions
        return null;
    };

    $scope.canAccessAccounts = function () {
        return !!$scope.getDefaultAccountState();
    };

    $scope.getDefaultCampaignState = function () {
        // keep the same tab if possible
        if ($state.includes('**.sources')) {
            return 'main.campaigns.sources';
        }
        if ($state.includes('**.history') && $scope.hasPermission('zemauth.campaign_history_view')) {
            return 'main.campaigns.history';
        }
        if ($state.includes('**.settings')) {
            return 'main.campaigns.settings';
        }
        if ($state.includes('**.budget') || $state.includes('**.credit')) {
            return 'main.campaigns.budget';
        }

        // otherwise get default state
        return 'main.campaigns.ad_groups';
    };

    $scope.canAccessCampaigns = function () {
        return !!$scope.getDefaultCampaignState();
    };

    $scope.getDefaultAdGroupState = function () {
        // keep the same tab if possible
        if ($state.includes('**.sources')) {
            return 'main.adGroups.sources';
        }
        if ($state.includes('**.history') && $scope.hasPermission('zemauth.ad_group_history_view')) {
            return 'main.adGroups.history';
        }
        if ($state.includes('**.settings') && $scope.hasPermission('dash.settings_view')) {
            return 'main.adGroups.settings';
        }
        if ($state.includes('**.publishers')) {
            return 'main.adGroups.publishers';
        }

        // otherwise get default state
        return 'main.adGroups.ads';
    };

    $scope.dateRange = zemDataFilterService.getDateRange();
    $scope.dateRangeOptions = {
        maxDate: moment().endOf('month'),
        ranges: zemHeaderDateRangePickerService.getPredefinedRanges(),
        opens: 'left',
        applyClass: 'btn-primary',
        eventHandlers: {
            'apply.daterangepicker': function () {
                zemDataFilterService.setDateRange($scope.dateRange);
            },
        },
    };
    zemDataFilterService.onDateRangeUpdate(function (event, updatedDateRange) {
        $scope.dateRange = updatedDateRange;
    });

    $scope.breadcrumb = [];

    $scope.setBreadcrumbAndTitle = function (breadcrumb, title) {
        var dashboardTitle = 'Zemanta';
        $scope.breadcrumb = breadcrumb;
        if ($scope.canAccessAllAccounts() && $scope.accountsAccess.accountsCount > 0) {
            $scope.breadcrumb.unshift({
                name: $scope.getBreadcrumbAllAccountsName(),
                state: $scope.getDefaultAllAccountsState(),
                disabled: !$scope.canAccessAllAccounts(),
            });
        }

        $document.prop('title', title + ' | ' + ($window.zOne.whitelabel && $window.zOne.whitelabel.dashboardTitle || dashboardTitle));
    };

    $scope.getBreadcrumbAllAccountsName = function () {
        if ($scope.hasPermission('dash.group_account_automatically_add')) {
            return 'All accounts';
        }

        return 'My accounts';
    };

    $scope.setModels = function (models) {
        $scope.account = null;
        $scope.campaign = null;
        $scope.adGroup = null;

        if (models) {
            if (models.hasOwnProperty('account')) {
                $scope.account = models.account;
            }
            if (models.hasOwnProperty('campaign')) {
                $scope.campaign = models.campaign;
            }
            if (models.hasOwnProperty('adGroup')) {
                $scope.adGroup = models.adGroup;
            }
        }
    };

    $scope.setPublisherFilterVisible = function (visible) {
        $scope.enablePublisherFilter = visible;
    };

    $scope.isChartVisible = function () {
        return $state.is('main.adGroups.ads') ||
            $state.is('main.adGroups.sources') ||
            $state.is('main.adGroups.publishers') ||
            $state.is('main.campaigns.ad_groups') ||
            $state.is('main.campaigns.sources') ||
            $state.is('main.accounts.campaigns') ||
            $state.is('main.accounts.sources') ||
            $state.is('main.allAccounts.accounts') ||
            $state.is('main.allAccounts.sources');
    };

    $scope.getAdGroupStatusClass = function (adGroup) {
        if (adGroup.reloading) {
            return 'adgroup-status-reloading-icon';
        }

        if (adGroup.active === constants.infoboxStatus.STOPPED) {
            return 'adgroup-status-stopped-icon';
        } else if (adGroup.active === constants.infoboxStatus.LANDING_MODE) {
            return ($state.includes('main.adGroups', {id: adGroup.id.toString()})) ?
                'adgroup-status-landing-mode-selected-icon' : 'adgroup-status-landing-mode-icon';
        } else if (adGroup.active === constants.infoboxStatus.INACTIVE) {
            return 'adgroup-status-inactive-icon';
        } else if (adGroup.active === constants.infoboxStatus.AUTOPILOT) {
            return 'adgroup-status-autopilot-icon';
        }

        return 'adgroup-status-active-icon';
    };

    $scope.isMetricInChartData = function (metric, chartData) {
        if (!chartData || !chartData.groups) return false;
        for (var i = 0; i < chartData.groups.length; i++) {
            var seriesData = chartData.groups[i].seriesData;
            if (!seriesData) return false;
            if (!seriesData.hasOwnProperty(metric)) return false;
        }
        return true;
    };

    $scope.requestDemo = function () {
        $uibModal.open({
            component: 'zemDemoRequest',
            windowClass: 'modal-default-legacy',
            backdrop: 'static',
            keyboard: false,
        });
    };

    $scope.$on('$stateChangeSuccess', function () {
        $scope.currentRoute = $state.current;

        // Redirect from default state
        var state = null;
        var id = $state.params.id;

        if ($state.is('main.allAccounts')) {
            state = $scope.getDefaultAllAccountsState();
        } else if ($state.is('main.accounts')) {
            state = $scope.getDefaultAccountState();
        } else if ($state.is('main.campaigns')) {
            state = $scope.getDefaultCampaignState();
        } else if ($state.is('main.adGroups')) {
            state = $scope.getDefaultAdGroupState();
        } else if ($state.is('main') && $scope.accountsAccess.hasAccounts) {
            if ($scope.canAccessAllAccounts() && $scope.accountsAccess.accountsCount > 1) {
                state = 'main.allAccounts.accounts';
            } else {
                id = $scope.accountsAccess.defaultAccountId;
                state = $scope.getDefaultAccountState();
            }
        }

        if (state) {
            $state.go(state, {id: id}, {location: 'replace'});
        }
    });

    zemNavigationService.onUpdate($scope, function () {
        $scope.accounts = zemNavigationService.getAccounts();
    });

    zemNavigationService.onLoading($scope, function (e, isLoading) {
        $scope.loadSidebarInProgress = isLoading;
    });

    var filteredSourcesUpdateHandler = zemDataFilterService.onFilteredSourcesUpdate(zemNavigationService.reload);
    var filteredAgenciesUpdateHandler = zemDataFilterService.onFilteredAgenciesUpdate(zemNavigationService.reload);
    var filteredAccountTypesUpdateHandler = zemDataFilterService.onFilteredAccountTypesUpdate(
        zemNavigationService.reload
    );
    var filteredPublisherStatusUpdateHandler = zemDataFilterService.onFilteredPublisherStatusUpdate(
        function (event, status) {
            $scope.setPublisherFilterVisible(status);
        }
    );
    $scope.$on('$destroy', function () {
        filteredSourcesUpdateHandler();
        filteredAgenciesUpdateHandler();
        filteredAccountTypesUpdateHandler();
        filteredPublisherStatusUpdateHandler();
    });
});
