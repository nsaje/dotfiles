/*globals oneApp,moment,$*/
function getDateRanges() {
    var result = {};
    var i = 0;
    var monthsCount = 3;
    var formatStr = 'MMMM YYYY';

    result['Today'] = [moment().startOf('day'), moment().endOf('day')];
    result['Yesterday'] = [moment().subtract('days', 1).startOf('day'), moment().subtract('days', 1).endOf('day')];
    result['This week'] = [moment().startOf('week'), moment()];
    result['Previous week'] = [moment().subtract('days', 7).startOf('week'), moment().subtract('days', 7).endOf('week')];
    result['Last 14 days'] = [moment().subtract('days', 14), moment()];
    result['This month'] = [moment().startOf('month'), moment()];
    result['Last 30 Days'] = [moment().subtract('days', 29), moment()];

    for (i = 0; i < monthsCount; i++) {
        result[moment().subtract('month', i+1).format(formatStr)] = [moment().subtract('month', i+1).startOf('month'), moment().subtract('month', i+1).endOf('month')];
    }

    result['Year to date'] = [moment().startOf('year'), moment()];
    
    return result;
}

oneApp.controller('MainCtrl', ['$scope', '$state', '$location', '$document', 'api', function ($scope, $state, $location, $document, api) {
    $scope.tabs = [
        {heading: 'Content Ads', route: 'adGroups.ads', active: true},
        {heading: 'Networks', route: 'adGroups.networks', active: false},
        {heading: 'Settings', route: 'adGroups.settings', active: false}
    ];
    $scope.accounts = null;
    $scope.user = null;
    $scope.currentRoute = $scope.current;
    $scope.inputDateFormat = 'M/D/YYYY';
    $scope.maxDate = moment();
    $scope.maxDateStr = $scope.maxDate.format('YYYY-MM-DD');
    $scope.dateRanges = getDateRanges();
    $scope.adGroupData = {};

    $scope.setAdGroupData = function (key, value) {
        var data = $scope.adGroupData[$state.params.id] || {};
        data[key] = value;
        $scope.adGroupData[$state.params.id] = data;
    };

    $scope.dateRange = {
        startDate: moment().subtract('day', 30).hours(0).minutes(0).seconds(0).milliseconds(0),
        endDate: moment().hours(0).minutes(0).seconds(0).milliseconds(0)
    };

    $scope.breadcrumb = [];

    $scope.setBreadcrumb = function () {
        if (!$scope.accounts) {
            return;
        }

        $scope.accounts.forEach(function (account) {
            account.campaigns.forEach(function (campaign) {
                campaign.adGroups.forEach(function (adGroup) {
                    if (adGroup.id.toString() === $state.params.id) {
                        $scope.breadcrumb = [account.name, campaign.name, adGroup.name];

                        // set page title
                        $document.prop('title', adGroup.name + ' - ' + campaign.name + ' | Zemanta');
                    }
                });
            });
        });
    };

    $scope.getCurrentParams = function () {
        var str = [];
        var params = $location.search();

        for (var p in params) {
            if (params.hasOwnProperty(p)) {
                str.push(encodeURIComponent(p) + "=" + encodeURIComponent(params[p]));
            }
        }

        if (str.length > 0) {
            return '?' + str.join("&");    
        } 
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
    
    $scope.stateChangeHandler = function (event, toState, toParams, fromState, fromParams) {
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

        if (!$.isEmptyObject(dateRange)) {
            $scope.dateRange = dateRange;
        }

        if (fromParams && fromParams.id && toParams && fromParams.id !== toParams.id) {
            // On ad group switch, get previous selected rows
            var data = $scope.adGroupData[$state.params.id] || {};

            $location.search('network_ids', data.networkIds && data.networkIds.join(','));
            $location.search('network_totals', data.networkTotals ? 1 : null);
            $location.search('article_ids', data.articleIds && data.articleIds.join(','));
            $location.search('article_totals', data.articleTotals ? 1 : null);

            $location.search('page', data.page)
        }
    };

    $scope.$on("$stateChangeSuccess", $scope.stateChangeHandler);

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
        if (!$.isEmptyObject(newValue) && !$.isEmptyObject(oldValue) &&  (newValue.startDate.valueOf() !== oldValue.startDate.valueOf() || newValue.endDate.valueOf() !== oldValue.endDate.valueOf())) {
            $location.search('start_date', $scope.dateRange.startDate ? $scope.dateRange.startDate.format() : null);
            $location.search('end_date', $scope.dateRange.endDate ? $scope.dateRange.endDate.format() : null);
        }
    });

    if ($scope.stateChangeFired) {
        $scope.stateChangeHandler();     
    }
}]);
