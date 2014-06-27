/*globals oneApp,moment,$*/
function getDateRanges() {
    var result = {};
    var i = 0;
    var monthsCount = 5;
    var formatStr = 'MMMM YYYY';

    result['Last 30 Days'] = [moment().subtract('days', 29), moment()];
    result[moment().format(formatStr) + ' (Current month)'] = [moment().startOf('month'), moment().endOf('month')];
    for (i = 0; i < monthsCount; i++) {
        result[moment().subtract('month', i+1).format(formatStr)] = [moment().subtract('month', i+1).startOf('month'), moment().subtract('month', i+1).endOf('month')];
    }
    result['Year to date'] = [moment().startOf('year'), moment()];
    
    return result;
}

oneApp.controller('MainCtrl', ['$scope', '$state', '$location', 'api', function ($scope, $state, $location, api) {
    $scope.tabs = [
        {heading: 'Content Ads', route: 'adGroups.ads', active: true},
        {heading: 'Networks', route: 'adGroups.networks', active: false},
        {heading: 'Settings', route: 'adGroups.settings', active: false}
    ];
    $scope.accounts = [];
    $scope.user = null;
    $scope.currentRoute = $scope.current;
    $scope.inputDateFormat = 'M/D/YYYY';
    $scope.maxDate = moment().subtract('days', 1);
    $scope.maxDateStr = $scope.maxDate.format('YYYY-MM-DD');
    $scope.dateRanges = getDateRanges();
    $scope.dateRange = {
        startDate: moment().subtract('day', 61).hours(0).minutes(0).seconds(0).milliseconds(0),
        endDate: moment().subtract('day', 1).hours(0).minutes(0).seconds(0).milliseconds(0)
    };

    $scope.breadcrumb = [];

    $scope.setBreadcrumb = function () {
        $scope.accounts.forEach(function (account) {
            account.campaigns.forEach(function (campaign) {
                campaign.adGroups.forEach(function (adGroup) {
                    if (adGroup.id.toString() === $state.params.id) {
                        $scope.breadcrumb = [account.name, campaign.name, adGroup.name];
                    }
                });
            });
        });
    };
    
    $scope.$on("$stateChangeSuccess", function() {
        $scope.currentRoute = $state.current;
        $scope.setBreadcrumb();
        $scope.tabs.forEach(function(tab) {
            tab.active = $state.is(tab.route);
        });

        var startDate = $location.search().start_date;
        var endDate = $location.search().end_date;
        var dateRange = {};

        if (startDate !== undefined && $scope.startDate !== startDate) {
			dateRange.startDate = moment(startDate);
        }

        if (endDate !== undefined && $scope.endDate !== endDate) {
			dateRange.endDate = moment(endDate);
        }

        if (!$.isEmptyObject($scope.dateRange)) {
            $scope.dateRange = dateRange;
        }
    });

    api.navData.list().then(function (data) {
        $scope.accounts = data;

        if ($state.current.abstract) {
            if ($scope.accounts && $scope.accounts.length) {
                $state.go('adGroups.ads', {id: $scope.accounts[0].campaigns[0].adGroups[0].id});
            }
        }
    });

    api.user.get('current').then(function (data) {
        $scope.user = data;
    });

    $scope.$watch('accounts', function (newValue, oldValue) {
        $scope.setBreadcrumb();
    });

    $scope.$watch('dateRange', function (newValue, oldValue) {
        if (newValue.startDate.valueOf() !== oldValue.startDate.valueOf() || newValue.endDate.valueOf() !== oldValue.endDate.valueOf()) {
            $location.search('start_date', $scope.dateRange.startDate ? $scope.dateRange.startDate.format() : null);
            $location.search('end_date', $scope.dateRange.endDate ? $scope.dateRange.endDate.format() : null);
        }
    });
}]);
