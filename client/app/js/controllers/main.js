/*globals oneApp,$*/
oneApp.controller('MainCtrl', ['$scope', '$state', '$location', '$document', 'api', 'zemMoment', 'user', 'accounts', function ($scope, $state, $location, $document, api, zemMoment, user, accounts) {
    $scope.accounts = accounts;
    $scope.user = user;
    $scope.currentRoute = $scope.current;
    $scope.inputDateFormat = 'M/D/YYYY';
    $scope.maxDate = zemMoment();
    $scope.maxDateStr = $scope.maxDate.format('YYYY-MM-DD');

    $scope.adGroupData = {};

    if (!$state.params.id && $scope.accounts && $scope.accounts.length) {
        $state.go('main.adGroups.ads', {id: $scope.accounts[0].campaigns[0].adGroups[0].id});
    }

    $scope.hasPermission = function (permission) {
        return $scope.user.permissions.indexOf(permission) >= 0;
    };

    $scope.getDateRanges = function () {
        var result = {};
        var i = 0;
        var monthsCount = 3;
        var formatStr = 'MMMM YYYY';
        var currentMonth = null;

        if ($scope.hasPermission('reports.fewer_daterange_options')) {
            result['Yesterday'] = [zemMoment().subtract('days', 1).startOf('day'), zemMoment().subtract('days', 1).endOf('day')];
            currentMonth = zemMoment().startOf('month');
            result[currentMonth.format('MMMM')] = [currentMonth, zemMoment().subtract('days', 1)];
            result['Last 30 Days'] = [zemMoment().subtract('days', 29), zemMoment().subtract('days', 1)];

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
        $scope.maxDate = zemMoment().subtract('day', 1);
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
        $document.prop('title', title + ' | Zemanta');
    };

    $scope.updateAccounts = function (adGroupId, newAdGroupName) {
        if (!$scope.accounts || !adGroupId || !newAdGroupName) {
            return;
        }

        $scope.accounts.forEach(function (account) {
            account.campaigns.forEach(function (campaign) {
                campaign.adGroups.forEach(function (adGroup) {
                    if (adGroup.id.toString() === adGroupId.toString()) {
                        adGroup.name = newAdGroupName;
                    }
                });
            });
        });
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
