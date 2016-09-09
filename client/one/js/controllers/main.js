/* globals $, angular, constants */
angular.module('one.legacy').controller('MainCtrl', ['$scope', '$state', '$location', '$document', '$q', '$uibModal', '$uibModalStack', '$timeout', '$window', 'zemMoment', 'userService', 'user', 'zemUserSettings', 'api', 'zemFilterService', 'zemFullStoryService', 'zemIntercomService', 'zemSupportHeroService', 'zemNavigationService', 'accountsAccess', 'redesignHelpersService', function ($scope, $state, $location, $document, $q, $uibModal, $uibModalStack, $timeout, $window, zemMoment, userService, user, zemUserSettings, api, zemFilterService, zemFullStoryService, zemIntercomService, zemSupportHeroService, zemNavigationService, accountsAccess, redesignHelpersService) { // eslint-disable-line max-len
    $scope.accountsAccess = accountsAccess;
    $scope.accounts = [];

    $scope.user = user;
    $scope.currentRoute = $scope.current;
    $scope.inputDateFormat = 'M/D/YYYY';
    $scope.maxDate = zemMoment().endOf('month');
    $scope.enablePublisherFilter = false;
    $scope.showSelectedPublisher = null;
    $scope.localStoragePrefix = 'main';

    $scope.adGroupData = {};
    $scope.account = null;
    $scope.campaign = null;
    $scope.adGroup = null;

    $scope.graphVisible = true;
    $scope.navigationPaneVisible = false;

    $scope.liveStreamOn = false;

    $scope.hasPermission = userService.hasPermission;
    $scope.isPermissionInternal = userService.isPermissionInternal;

    $scope.hasAgency = function () {
        if ($scope.user.agency) {
            return true;
        }
        return false;
    };

    $scope.toggleGraph = function () {
        $scope.graphVisible = !$scope.graphVisible;
        $scope.reflowGraph(0);
    };

    $scope.toggleNavigationPane = function () {
        $scope.navigationPaneVisible = !$scope.navigationPaneVisible;
        $scope.reflowGraph(0);
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

        // otherwise get default state
        return 'main.adGroups.ads';
    };

    $scope.getDateRanges = function () {
        var result = {};

        result.Yesterday = [
            zemMoment().subtract(1, 'days').startOf('day'),
            zemMoment().subtract(1, 'days').endOf('day'),
        ];

        result['Last 7 Days'] = [zemMoment().subtract(7, 'days'), zemMoment().subtract(1, 'days')];
        result['Last 30 Days'] = [zemMoment().subtract(30, 'days'), zemMoment().subtract(1, 'days')];

        result['This Month'] = [zemMoment().startOf('month'), zemMoment().endOf('month')];
        result['Last Month'] = [
            zemMoment().subtract(1, 'month').startOf('month'),
            zemMoment().subtract(1, 'month').endOf('month'),
        ];

        result['Year to date'] = [zemMoment().startOf('year'), zemMoment().subtract(1, 'days')];
        return result;
    };

    $scope.setDateRangeFromSearch = function () {
        var startDate = $location.search().start_date;
        var endDate = $location.search().end_date;
        var dateRange = {};

        if (startDate !== undefined && $scope.startDate !== startDate) {
            dateRange.startDate = zemMoment(startDate);
        }

        if (endDate !== undefined && $scope.endDate !== endDate) {
            dateRange.endDate = zemMoment(endDate);
        }

        if (!$.isEmptyObject(dateRange)) {
            $scope.dateRange = dateRange;
        }
    };

    $scope.dateRange = {
        startDate: zemMoment().subtract(29, 'day').hours(0).minutes(0).seconds(0).milliseconds(0),
        endDate: zemMoment().subtract(1, 'day').endOf('day'),
    };

    $scope.setDateRangeFromSearch();

    $scope.dateRangeOptions = {
        maxDate: $scope.maxDate.format('YYYY-MM-DD'),
        ranges: $scope.getDateRanges(),
        opens: 'left',
        applyClass: 'btn-primary',
    };

    $scope.breadcrumb = [];

    $scope.setBreadcrumbAndTitle = function (breadcrumb, title) {
        $scope.breadcrumb = breadcrumb;
        if ($scope.canAccessAllAccounts() && $scope.accountsAccess.accountsCount > 0) {
            $scope.breadcrumb.unshift({
                name: $scope.getBreadcrumbAllAccountsName(),
                state: $scope.getDefaultAllAccountsState(),
                disabled: !$scope.canAccessAllAccounts(),
            });
        }

        $document.prop('title', title + ' | Zemanta');
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
        var modalInstance = $uibModal.open({
            templateUrl: '/partials/request_demo_modal.html',
            controller: 'RequestDemoModalCtrl',
            windowClass: 'modal-default',
            scope: $scope,
        });
        return modalInstance;
    };

    $scope.allowLivestream = function () {
        $scope.liveStreamOn = true;
        if (!$window.FS) { return; }
        api.liveStream.allow($window.FS.getCurrentSessionURL());
    };

    $scope.$on('$stateChangeSuccess', function () {
        $scope.currentRoute = $state.current;
        $scope.setDateRangeFromSearch();

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
            $state.go(state, {id: id});
        }
    });

    $document.bind('keyup', function (event) {
        if (!event) {
            return;
        }

        event.preventDefault();

        if (String.fromCharCode(event.keyCode).toLowerCase() !== 'f') {
            return;
        }

        // nav search shortcut
        var el = $('#nav-search .select2-container');

        if (document.activeElement.tagName.toLowerCase() === 'input' ||
            document.activeElement.tagName.toLowerCase() === 'select' ||
            document.activeElement.tagName.toLowerCase() === 'textarea') {
            // input element in focus
            return;
        }

        if ($uibModalStack.getTop()) {
            // some modal window exists
            return;
        }

        if (el) {
            el.select2('open');
        }
    });

    $scope.$watch('dateRange', function (newValue, oldValue) {
        if ($.isEmptyObject(newValue) || $.isEmptyObject(oldValue)) {
            return;
        }

        if (newValue.startDate.valueOf() === oldValue.startDate.valueOf() &&
            newValue.endDate.valueOf() === oldValue.endDate.valueOf()) {
            return;
        }

        $location.search('start_date',
            $scope.dateRange.startDate ? $scope.dateRange.startDate.format('YYYY-MM-DD') : null);

        $location.search('end_date',
            $scope.dateRange.endDate ? $scope.dateRange.endDate.format('YYYY-MM-DD') : null);
    });

    $scope.getShowArchived = function () {
        return zemFilterService.getShowArchived();
    };

    zemNavigationService.onUpdate($scope, function () {
        $scope.accounts = zemNavigationService.getAccounts();
    });

    zemNavigationService.onLoading($scope, function (e, isLoading) {
        $scope.loadSidebarInProgress = isLoading;
    });

    $scope.$watch(zemFilterService.getFilteredSources, function (newValue, oldValue) {
        if (angular.equals(newValue, oldValue)) { return; }
        zemNavigationService.reload();
    }, true);

    $scope.$watch(zemFilterService.getFilteredAgencies, function (newValue, oldValue) {
        if (angular.equals(newValue, oldValue)) { return; }
        zemNavigationService.reload();
    }, true);

    $scope.$watch(zemFilterService.getFilteredAccountTypes, function (newValue, oldValue) {
        if (angular.equals(newValue, oldValue)) { return; }
        zemNavigationService.reload();
    }, true);

    $scope.$watch(zemFilterService.getShowBlacklistedPublishers, function (newValue, oldValue) {
        if (angular.equals(newValue, oldValue)) {
            return;
        }
        $scope.setPublisherFilterVisible(newValue);
    }, true);


    $scope.init = function () {
        zemFullStoryService.identify($scope.user);
        zemIntercomService.boot($scope.user);
        zemSupportHeroService.boot($scope.user);
        zemNavigationService.reload();

        var userSettings = zemUserSettings.getInstance($scope, $scope.localStoragePrefix);
        userSettings.registerGlobal('graphVisible');
        userSettings.registerGlobal('navigationPaneVisible');

        if (document.referrer.indexOf(location.protocol + '//' + location.host) === 0 &&
            document.referrer.indexOf('/signin') > 0) {
            $scope.navigationPaneVisible = false;
        }
    };

    $scope.init();


    // TODO: Remove once redesign is finished
    $scope.userCanSeeNewLayout = redesignHelpersService.canSeeNewLayout;
    $scope.toggleNewLayout = redesignHelpersService.toggleNewLayout;
    redesignHelpersService.setBodyThemeClass();
}]);
