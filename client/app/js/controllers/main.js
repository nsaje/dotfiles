/*globals oneApp,$*/
oneApp.controller('MainCtrl', ['$scope', '$state', '$location', '$document', 'zemMoment', 'user', 'accounts', function ($scope, $state, $location, $document, zemMoment, user, accounts) {
    $scope.accounts = accounts;
    $scope.user = user;
    $scope.currentRoute = $scope.current;
    $scope.inputDateFormat = 'M/D/YYYY';
    $scope.maxDate = zemMoment();
    $scope.maxDateStr = $scope.maxDate.format('YYYY-MM-DD');

    $scope.adGroupData = {};

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
    
    $scope.canAccessAllAccounts = function () {
        return $scope.hasPermission('zemauth.all_accounts_accounts_view');
    };

    $scope.canAccessAccounts = function () {
        return $scope.hasPermission('zemauth.accounts_campaigns_view');
    };

    $scope.canAccessCampaigns = function () {
        return $scope.hasPermission('zemauth.campaign_settings_view')
    };

    // Redirect from default state
    if ($state.is('main') && $scope.accounts && $scope.accounts.length) {
        if ($scope.canAccessAllAccounts()) {
            $state.go('main.allAccounts.accounts');
        } else {
            $state.go('main.adGroups.ads', {id: $scope.accounts[0].campaigns[0].adGroups[0].id});
        }
    }

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

    $scope.breadcrumb = [];

    $scope.setBreadcrumbAndTitle = function (breadcrumb, title) {
        $scope.breadcrumb = breadcrumb;
        $scope.breadcrumb.unshift({name: 'All accounts', state: 'main.allAccounts.accounts', disabled: !$scope.canAccessAllAccounts()});

        $document.prop('title', title + ' | Zemanta');
    };

    $scope.$on("$stateChangeSuccess", function (event, toState, toParams, fromState, fromParams) {
        $scope.currentRoute = $state.current;
        $scope.setDateRangeFromSearch();
    });

    $scope.$watch('dateRange', function (newValue, oldValue) {
        if (!$.isEmptyObject(newValue) && !$.isEmptyObject(oldValue) &&  (newValue.startDate.valueOf() !== oldValue.startDate.valueOf() || newValue.endDate.valueOf() !== oldValue.endDate.valueOf())) {
            $location.search('start_date', $scope.dateRange.startDate ? $scope.dateRange.startDate.format() : null);
            $location.search('end_date', $scope.dateRange.endDate ? $scope.dateRange.endDate.format() : null);
        }
    });
}]);
