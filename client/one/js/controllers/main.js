/*globals oneApp,$,FS*/
oneApp.controller('MainCtrl',
    ['$scope',
     '$state',
     '$location',
     '$document',
     '$q',
     '$modalStack',
     'zemMoment',
     'user',
     'zemUserSettings',
     'accounts',
     'api',
     'zemFilterService',
     'zemFullStoryService',
     'zemIntercomService',
      function (
        $scope,
        $state,
        $location,
        $document,
        $q,
        $modalStack,
        zemMoment,
        user,
        zemUserSettings,
        accounts,
        api,
        zemFilterService,
        zemFullStoryService,
        zemIntercomService
) {
    $scope.accounts = accounts;
    $scope.user = user;
    $scope.currentRoute = $scope.current;
    $scope.inputDateFormat = 'M/D/YYYY';
    $scope.maxDate = zemMoment();
    $scope.maxDateStr = $scope.maxDate.format('YYYY-MM-DD');
    $scope.enablePublisherFilter = false;
    $scope.showSelectedPublisher = null;

    // TODO: move to localstorage
    $scope.infoboxVisible = false;

    $scope.remindToAddBudget = $q.defer(); 

    $scope.adGroupData = {};
    $scope.account = null;
    $scope.campaign = null;
    $scope.adGroup = null;

    $scope.user.automaticallyCreateAdGroup = false;

    $scope.refreshNavData = function (accounts) {
        $scope.accounts = accounts;
    };

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

    $scope.toggleInfoboxVisibility = function () {
        $scope.infoboxVisible = !$scope.infoboxVisible;
    }

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
        if ($scope.hasPermission('zemauth.campaign_budget_management_view')) {
            return 'main.campaings.budget';
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

        result['Yesterday'] = [zemMoment().subtract('days', 1).startOf('day'), zemMoment().subtract('days', 1).endOf('day')];
        result['Last 30 Days'] = [zemMoment().subtract('days', 30), zemMoment().subtract('days', 1)];
        currentMonth = zemMoment().startOf('month');
        result[currentMonth.format(formatStr)] = [currentMonth, zemMoment().subtract('days', 1)];

        for (i = 0; i < monthsCount; i++) {
            result[zemMoment().subtract('month', i+1).format(formatStr)] = [zemMoment().subtract('month', i+1).startOf('month'), zemMoment().subtract('month', i+1).endOf('month')];
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
        endDate: zemMoment().subtract('day', 1).endOf('day')
    };

    $scope.setDateRangeFromSearch();
    $scope.dateRanges = $scope.getDateRanges();

    $scope.breadcrumb = [];

    $scope.setBreadcrumbAndTitle = function (breadcrumb, title) {
        $scope.breadcrumb = breadcrumb;
        if ($scope.canAccessAllAccounts() && $scope.accounts.length) {
            $scope.breadcrumb.unshift({name: 'All accounts', state: $scope.getDefaultAllAccountsState(), disabled: !$scope.canAccessAllAccounts()});
        }

        $document.prop('title', title + ' | Zemanta');
    };

    $scope.setAccount = function (account) {
        $scope.account = account;
    };

    $scope.setCampaign = function (campaign) {
        $scope.campaign = campaign;
    };

    $scope.setAdGroup = function (adGroup) {
        $scope.adGroup = adGroup;
    };

    $scope.setPublisherFilterVisible = function (visible) {
        $scope.enablePublisherFilter = visible;
    };

    $scope.$on("$stateChangeSuccess", function (event, toState, toParams, fromState, fromParams) {
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
        } else if ($state.is('main') && $scope.accounts && $scope.accounts.length) {
            if ($scope.canAccessAllAccounts()) {
                state = 'main.allAccounts.accounts';
            } else {
                $scope.accounts.some(function (account) {
                    id = account.id;

                    if (id && account.archived === false) {
                        return true;
                    }

                    return false;
                });

                state = $scope.getDefaultAccountState();
            }
        }

        if (state) {
            $state.go(state, {id: id});
        }
    });

    $document.bind('keyup', function (e) {
        if (e) {
            if (String.fromCharCode(e.keyCode).toLowerCase() === 'f') {
                // nav search shortcut
                var el = $('#nav-search .select2-container');

                if (document.activeElement.tagName.toLowerCase() === 'input' ||
                    document.activeElement.tagName.toLowerCase() === 'select' ||
                    document.activeElement.tagName.toLowerCase() === 'textarea') {
                    // input element in focus
                    return;
                }

                if (!!$modalStack.getTop()) {
                    // some modal window exists
                    return;
                }

                if (el) {
                    el.select2('open');
                }
            }

            e.preventDefault();
        }
    });

    $scope.$watch('dateRange', function (newValue, oldValue) {
        if (!$.isEmptyObject(newValue) && !$.isEmptyObject(oldValue) && (newValue.startDate.valueOf() !== oldValue.startDate.valueOf() || newValue.endDate.valueOf() !== oldValue.endDate.valueOf())) {
            $location.search('start_date', $scope.dateRange.startDate ? $scope.dateRange.startDate.format('YYYY-MM-DD') : null);
            $location.search('end_date', $scope.dateRange.endDate ? $scope.dateRange.endDate.format('YYYY-MM-DD') : null);
        }
    });

    $scope.getShowArchived = function () {
        return zemFilterService.getShowArchived();
    };

    $scope.getConversionPixelTag = function (url) {
        return '<img src="' + url + '" height="1" width="1" border="0" alt="" />';
    };

    $scope.$watch(zemFilterService.getFilteredSources, function (newValue, oldValue) {
        if (angular.equals(newValue, oldValue)) {
            return;
        }

        $scope.loadSidebarInProgress = true;
        api.navData.list().then(function (accounts) {
            $scope.refreshNavData(accounts);
        })
        .finally(function () {
            $scope.loadSidebarInProgress = false;
        });
    }, true);

    $scope.$watch(zemFilterService.getShowBlacklistedPublishers, function (newValue, oldValue) {
        if (angular.equals(newValue, oldValue)) {
            return;
        }
        $scope.setPublisherFilterVisible(newValue);
    }, true);

    zemFullStoryService.identify($scope.user);
    zemIntercomService.boot($scope.user);

}]);
