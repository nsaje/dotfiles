/*globals oneApp,$*/
oneApp.controller('MainCtrl', ['$scope', '$state', '$location', '$document', 'zemMoment', 'user', 'accounts', 'localStorageService', 'api', function ($scope, $state, $location, $document, zemMoment, user, accounts, localStorageService, api) {
    $scope.accounts = accounts;
    $scope.user = user;
    $scope.currentRoute = $scope.current;
    $scope.inputDateFormat = 'M/D/YYYY';
    $scope.maxDate = zemMoment();
    $scope.maxDateStr = $scope.maxDate.format('YYYY-MM-DD');

    $scope.showArchived = false;

    $scope.adGroupData = {};
    $scope.account = null;
    $scope.campaign = null;
    $scope.adGroup = null;

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

    $scope.getDefaultAllAccountsState = function () {
        var result = null;

        if ($scope.hasPermission('zemauth.all_accounts_accounts_view')) {
            result = 'main.allAccounts.accounts';
        } else if ($scope.hasPermission('zemauth.all_accounts_sources_view')) {
            result = 'main.allAccounts.sources';
        } else if ($scope.hasPermission('zemauth.all_accounts_budget_view')) {
            result = 'main.allAccounts.budget';
        }

        return result;
    };

    $scope.canAccessAllAccounts = function () {
        return !!$scope.getDefaultAllAccountsState();
    };

    $scope.getDefaultAccountState = function () {
        var result = null;

        if ($scope.hasPermission('zemauth.account_campaigns_view')) {
            result = 'main.accounts.campaigns';
        } else if ($scope.hasPermission('zemauth.account_sources_view')) {
            result = 'main.accounts.sources';
        } else if ($scope.hasPermission('zemauth.account_agency_view')) {
            result = 'main.accounts.agency';
        } else if ($scope.hasPermission('zemauth.account_budget_view')) {
            result = 'main.accounts.budget';
        }

        return result;
    };

    $scope.canAccessAccounts = function () {
        return !!$scope.getDefaultAccountState();
    };

    $scope.getDefaultCampaignState = function () {
        if ($state.includes('main.campaigns.*')) {
            return $state.current.name;
        }

        var result = null;

        if ($scope.hasPermission('zemauth.campaign_ad_groups_view')) {
            result = 'main.campaigns.ad_groups';
        } else if ($scope.hasPermission('zemauth.campaign_sources_view')) {
            result = 'main.campaings.sources';
        } else if ($scope.hasPermission('zemauth.campaign_settings_view')) {
            result = 'main.campaigns.agency';
        } else if ($scope.hasPermission('zemauth.campaign_budget_management_view')) {
            result = 'main.campaings.budget';
        }

        return result;
    };

    $scope.canAccessCampaigns = function () {
        return !!$scope.getDefaultCampaignState();
    };

    $scope.getDefaultAdGroupState = function () {
        if ($state.includes('main.adGroups.*')) {
            return $state.current.name;
        }

        return 'main.adGroups.ads';
    };

    $scope.getDateRanges = function () {
        var result = {};
        var i = 0;
        var monthsCount = 3;
        var formatStr = 'MMMM YYYY';
        var currentMonth = null;

        if ($scope.hasPermission('reports.fewer_daterange_options')) {
            result['Yesterday'] = [zemMoment().subtract('days', 1).startOf('day'), zemMoment().subtract('days', 1).endOf('day')];
            result['Last 30 Days'] = [zemMoment().subtract('days', 29), zemMoment().subtract('days', 1)];
            currentMonth = zemMoment().startOf('month');
            result[currentMonth.format(formatStr)] = [currentMonth, zemMoment().subtract('days', 1)];

            for (i = 0; i < monthsCount; i++) {
                result[zemMoment().subtract('month', i+1).format(formatStr)] = [zemMoment().subtract('month', i+1).startOf('month'), zemMoment().subtract('month', i+1).endOf('month')];
            }

            result['Year to date'] = [zemMoment().startOf('year'), zemMoment().subtract('days', 1)];
        } else {
            result['Today'] = [zemMoment().startOf('day'), zemMoment().endOf('day')];
            result['Yesterday'] = [zemMoment().subtract('days', 1).startOf('day'), zemMoment().subtract('days', 1).endOf('day')];
            result['This week'] = [zemMoment().startOf('week'), zemMoment()];
            result['Previous week'] = [zemMoment().subtract('days', 7).startOf('week'), zemMoment().subtract('days', 7).endOf('week')];
            result['Last 14 days'] = [zemMoment().subtract('days', 14), zemMoment()];
            result['This month'] = [zemMoment().startOf('month'), zemMoment()];
            result['Last 30 Days'] = [zemMoment().subtract('days', 29), zemMoment()];

            for (i = 0; i < monthsCount; i++) {
                result[zemMoment().subtract('month', i+1).format(formatStr)] = [zemMoment().subtract('month', i+1).startOf('month'), zemMoment().subtract('month', i+1).endOf('month')];
            }

            result['Year to date'] = [zemMoment().startOf('year'), $scope.maxDate];
        }

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

    if ($scope.hasPermission('reports.fewer_daterange_options')) {
        $scope.maxDateStr = $scope.maxDate.format('YYYY-MM-DD');
        $scope.dateRange = {
            startDate: zemMoment().subtract('day', 29).hours(0).minutes(0).seconds(0).milliseconds(0),
            endDate: zemMoment().subtract('day', 1).endOf('day')
        };
    } else {
        $scope.dateRange = {
            startDate: zemMoment().subtract('day', 30).hours(0).minutes(0).seconds(0).milliseconds(0),
            endDate: zemMoment().hours(0).minutes(0).seconds(0).milliseconds(0)
        };
    }

    $scope.setDateRangeFromSearch();
    $scope.dateRanges = $scope.getDateRanges();

    $scope.setShowArchived = function () {
        if (typeof $location.search().show_archived !== 'undefined') {
            $scope.showArchived = $location.search().show_archived === 'true';
        } else if (localStorageService.keys().indexOf('main.showArchived') >= 0 && $scope.hasPermission('zemauth.view_archived_entities')) {
            $scope.showArchived = localStorageService.get('main.showArchived') === 'true';
        }
    };

    $scope.setShowArchived();

    $scope.breadcrumb = [];

    $scope.setBreadcrumbAndTitle = function (breadcrumb, title) {
        $scope.breadcrumb = breadcrumb;
        if ($scope.canAccessAllAccounts()) {
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
                    if (account.campaigns && account.campaigns.length) {
                        account.campaigns.some(function (campaign) {
                            if (campaign.adGroups && campaign.adGroups.length) {
                                id = campaign.adGroups[0].id;
                                return true;
                            }
                        });
                    }

                    if (id) {
                        return true;
                    }
                });
                state = $scope.getDefaultAdGroupState();
            }
        }

        if (state) {
            $state.go(state, {id: id});
        }
    });

    $('#filter').on('click', function(e) {
        e.stopPropagation();
    });

    $document.bind('keyup', function (e) {
        if (e) {
            if (String.fromCharCode(e.keyCode).toLowerCase() === 'f') {
                var el = $('#nav-search .select2-container');

                if (document.activeElement.tagName.toLowerCase() === 'input' ||
                    document.activeElement.tagName.toLowerCase() === 'select' ||
                    document.activeElement.tagName.toLowerCase() === 'textarea') {
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
        if (!$.isEmptyObject(newValue) && !$.isEmptyObject(oldValue) &&  (newValue.startDate.valueOf() !== oldValue.startDate.valueOf() || newValue.endDate.valueOf() !== oldValue.endDate.valueOf())) {
            $location.search('start_date', $scope.dateRange.startDate ? $scope.dateRange.startDate.format('YYYY-MM-DD') : null);
            $location.search('end_date', $scope.dateRange.endDate ? $scope.dateRange.endDate.format('YYYY-MM-DD') : null);
        }
    });

    $scope.$watch('showArchived', function (newValue, oldValue) {
        if (oldValue !== newValue) {
            if ($scope.hasPermission('zemauth.view_archived_entities')) {
                $location.search('show_archived', newValue.toString());
                localStorageService.set('main.showArchived', newValue.toString());
            }
        }
    });
}]);
