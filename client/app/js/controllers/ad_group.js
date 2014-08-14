/*globals oneApp,$,moment*/
oneApp.controller('AdGroupCtrl', ['$scope', '$state', '$location', function ($scope, $state, $location) {
    $scope.tabs = [
        {heading: 'Content Ads', route: 'main.adGroups.ads', active: true, hidden: false},
        {heading: 'Media Sources', route: 'main.adGroups.sources', active: false, hidden: false},
        {heading: 'Settings', route: 'main.adGroups.settings', active: false, hidden: !$scope.hasPermission('dash.settings_view')}
    ];

    $scope.isAdGroupPaused = false;
    $scope.account = null;
    $scope.campaign = null;
    $scope.adGroup = null;

    // this function is used by ad_grou_ conrollers to set $scope.$scope.isAdGroupPaused
    $scope.setAdGroupPaused = function(val) {
        $scope.isAdGroupPaused = val;
    };

    $scope.setAdGroupData = function (key, value) {
        var data = $scope.adGroupData[$state.params.id] || {};
        data[key] = value;
        $scope.adGroupData[$state.params.id] = data;
    };

    $scope.getModels = function () {
        $scope.accounts.forEach(function (account) {
            account.campaigns.forEach(function (campaign) {
                campaign.adGroups.forEach(function (adGroup) {
                    if (adGroup.id.toString() === $state.params.id.toString()) {
                        $scope.account  = account;
                        $scope.campaign = campaign;
                        $scope.adGroup = adGroup;
                    }
                });
            });
        });
    };

    $scope.updateAccounts = function (newAdGroupName) {
        if (!$scope.accounts || !newAdGroupName) {
            return;
        }
        $scope.adGroup.name = newAdGroupName;
    };

    $scope.updateBreadcrumbAndTitle = function () {
        if (!$scope.accounts) {
            return;
        }
        $scope.setBreadcrumbAndTitle(
            [$scope.account.name, $scope.campaign.name, $scope.adGroup.name],
            $scope.adGroup.name + ' - ' + $scope.campaign.name
        );
    };

    $scope.tabs.forEach(function(tab) {
        tab.active = $state.is(tab.route);
    });

    if (!$scope.adGroupData.adGroupChange) {
        $scope.adGroupData.adGroupChange = true;
    } else {
        var data = $scope.adGroupData[$state.params.id];
        $location.search('source_ids', data && data.sourceIds && data.sourceIds.join(','));
        $location.search('source_totals', data && data.sourceTotals ? 1 : null);
        $location.search('page', data && data.page);
    }

    $scope.getModels();
    $scope.updateBreadcrumbAndTitle();
}]);
