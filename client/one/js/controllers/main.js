/* globals oneApp, $, angular */
oneApp.controller('MainCtrl', ['$scope', '$state', '$location', '$document', '$q', '$modalStack', '$timeout', 'zemMoment', 'user', 'zemUserSettings', 'api', 'zemFilterService', 'zemFullStoryService', 'zemIntercomService', 'zemNavigationService', 'accountsAccess', function ( $scope, $state, $location, $document, $q, $modalStack, $timeout, zemMoment, user, zemUserSettings, api, zemFilterService, zemFullStoryService, zemIntercomService, zemNavigationService, accountsAccess) {
    $scope.accountsAccess = accountsAccess;
    $scope.accounts = [];

    $scope.user = user;
    $scope.currentRoute = $scope.current;
    $scope.inputDateFormat = 'M/D/YYYY';
    $scope.maxDate = zemMoment();
    $scope.maxDateStr = $scope.maxDate.format('YYYY-MM-DD');
    $scope.enablePublisherFilter = false;
    $scope.showSelectedPublisher = null;
    $scope.localStoragePrefix = 'main';

    $scope.remindToAddBudget = $q.defer();

    $scope.adGroupData = {};
    $scope.account = null;
    $scope.campaign = null;
    $scope.adGroup = null;

    $scope.infoboxEnabled = false;
    $scope.infoboxVisible = false;
    $scope.graphVisible = true;
    $scope.navigationPaneVisible = true;

    $scope.user.automaticallyCreateAdGroup = false;

    $scope.hasPermission = function (permissions) {
        if (!permissions) {
            return false;
        }

        // can take string or array, returns true if user has any of the permissions
        if (typeof permissions === 'string') {
            permissions = [permissions];
        }

        return permissions.some(function (permission) {
            return Object.keys($scope.user.permissions).indexOf(permission) >= 0;
        });
    };

    $scope.isPermissionInternal = function (permission) {
        if (Object.keys($scope.user.permissions).indexOf(permission) < 0) {
            return false;
        }

        return !$scope.user.permissions[permission];
    };

    $scope.toggleInfobox = function () {
        $scope.infoboxVisible = !$scope.infoboxVisible;
        $scope.reflowGraph(0);
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

    $scope.canShowBudgetNotification = function () {
        return $scope.remindToAddBudget.promise;
    };

    $scope.getDefaultAccountState = function () {
        // keep the same tab if possible
        if ($state.includes('**.sources') && $scope.hasPermission('zemauth.account_sources_view')) {
            return 'main.accounts.sources';
        }
        if ($state.includes('**.agency') && $scope.hasPermission('zemauth.account_agency_view')) {
            return 'main.accounts.agency';
        }

        // otherwise get default state
        if ($scope.hasPermission('zemauth.account_campaigns_view')) {
            return 'main.accounts.campaigns';
        }
        if ($scope.hasPermission('zemauth.account_sources_view')) {
            return 'main.accounts.sources';
        }
        if ($scope.hasPermission('zemauth.account_agency_view')) {
            return 'main.accounts.agency';
        }

        // no permissions
        return null;
    };

    $scope.canAccessAccounts = function () {
        return !!$scope.getDefaultAccountState();
    };

    $scope.getDefaultCampaignState = function () {
        if ($state.includes('main.campaigns.*')) {
            return $state.current.name;
        }

        // keep the same tab if possible
        if ($state.includes('**.sources') && $scope.hasPermission('zemauth.campaign_sources_view')) {
            return 'main.campaigns.sources';
        }
        if ($state.includes('**.agency') && $scope.hasPermission('zemauth.campaign_agency_view')) {
            return 'main.campaigns.agency';
        }
        if ($state.includes('**.settings') && $scope.hasPermission('zemauth.campaign_settings_view')) {
            return 'main.campaigns.settings';
        }

        // otherwise get default state
        if ($scope.hasPermission('zemauth.campaign_ad_groups_view')) {
            return 'main.campaigns.ad_groups';
        }
        if ($scope.hasPermission('zemauth.campaign_sources_view')) {
            return 'main.campaings.sources';
        }
        if ($scope.hasPermission('zemauth.campaign_agency_view')) {
            return 'main.campaigns.agency';
        }
        if ($scope.hasPermission('zemauth.campaign_budget_view')) {
            return 'main.campaings.budget_plus';
        }
        if ($scope.hasPermission('zemauth.campaign_settings_view')) {
            return 'main.campaigns.settings';
        }

        // no permissions
        return null;
    };

    $scope.canAccessCampaigns = function () {
        return !!$scope.getDefaultCampaignState();
    };

    $scope.getDefaultAdGroupState = function () {
        if ($state.includes('main.adGroups.*')) {
            return $state.current.name;
        }

        // keep the same tab if possible
        if ($state.includes('**.sources')) {
            return 'main.adGroups.sources';
        }
        if ($state.includes('**.agency') && $scope.hasPermission('zemauth.ad_group_agency_tab_view')) {
            return 'main.adGroups.agency';
        }

        // otherwise get default state
        return 'main.adGroups.ads';
    };

    $scope.getDateRanges = function () {
        var result = {};
        var i = 0;
        var monthsCount = 3;
        var formatStr = 'MMMM YYYY';
        var currentMonth = null;

        result.Yesterday = [
            zemMoment().subtract('days', 1).startOf('day'),
            zemMoment().subtract('days', 1).endOf('day'),
        ];
        result['Last 30 Days'] = [zemMoment().subtract('days', 30), zemMoment().subtract('days', 1)];
        currentMonth = zemMoment().startOf('month');
        result[currentMonth.format(formatStr)] = [currentMonth, zemMoment().subtract('days', 1)];

        for (i = 0; i < monthsCount; i++) {
            result[zemMoment().subtract('month', i + 1).format(formatStr)] = [
                zemMoment().subtract('month', i + 1).startOf('month'),
                zemMoment().subtract('month', i + 1).endOf('month'),
            ];
        }

        result['Year to date'] = [zemMoment().startOf('year'), zemMoment().subtract('days', 1)];

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

    $scope.maxDateStr = $scope.maxDate.format('YYYY-MM-DD');
    $scope.dateRange = {
        startDate: zemMoment().subtract('day', 29).hours(0).minutes(0).seconds(0).milliseconds(0),
        endDate: zemMoment().subtract('day', 1).endOf('day'),
    };

    $scope.setDateRangeFromSearch();
    $scope.dateRanges = $scope.getDateRanges();

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

    $scope.isInfoboxEnabled = function () {
        // infobox will be visible only on certain views and
        // is entirely housed within main atm
        if ($state.is('main.campaigns.ad_groups') ||
            $state.is('main.campaigns.sources') ||
            $state.is('main.adGroups.adsPlus') ||
            $state.is('main.adGroups.sources') ||
            $state.is('main.adGroups.publishers') ||
            $state.is('main.accounts.campaigns') ||
            $state.is('main.accounts.sources') ||
            $state.is('main.allAccounts.accounts') ||
            $state.is('main.allAccounts.sources')) {
            return true;
        }

        return false;
    };

    $scope.hasInfoboxPermission = function () {
        if ($state.is('main.adGroups.adsPlus') ||
            $state.is('main.adGroups.sources') ||
            $state.is('main.adGroups.publishers')) {
            $scope.infoboxVisible = true;
            return $scope.hasPermission('zemauth.can_access_ad_group_infobox');
        }

        if ($state.is('main.campaigns.ad_groups') ||
            $state.is('main.campaigns.sources')) {
            $scope.infoboxVisible = true;
            return $scope.hasPermission('zemauth.can_access_campaign_infobox');
        }

        if ($state.is('main.accounts.campaigns') ||
            $state.is('main.accounts.sources')) {
            $scope.infoboxVisible = true;
            return $scope.hasPermission('zemauth.can_access_account_infobox');
        }

        if ($state.is('main.allAccounts.accounts') ||
            $state.is('main.allAccounts.sources')) {
            return $scope.hasPermission('zemauth.can_access_all_accounts_infobox');
        }

        return false;
    };

    $scope.$on('$stateChangeSuccess', function () {
        $scope.currentRoute = $state.current;
        $scope.setDateRangeFromSearch();

        // infobox will be visible only on certain views and
        // is entirely housed within main atm
        $scope.infoboxEnabled = $scope.isInfoboxEnabled() && $scope.hasInfoboxPermission();

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

        if ($modalStack.getTop()) {
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
        if (angular.equals(newValue, oldValue)) {
            return;
        }

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
        zemNavigationService.reload();

        var userSettings = zemUserSettings.getInstance($scope, $scope.localStoragePrefix);
        userSettings.registerGlobal('graphVisible');
        userSettings.registerGlobal('navigationPaneVisible');
        if ($state.is('main.allAccounts.accounts') ||
            $state.is('main.allAccounts.sources')) {
            userSettings.registerGlobal('infoboxVisible');
        }
    };

    $scope.init();
}]);
