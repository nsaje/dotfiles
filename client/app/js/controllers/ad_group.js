/*globals oneApp,$,moment*/
oneApp.controller('AdGroupCtrl', ['$scope', '$state', '$location', 'api', function ($scope, $state, $location, api) {
    $scope.tabs = [
        {heading: 'Content Ads', route: 'main.adGroups.ads', active: true, hidden: false},
        {heading: 'Media Sources', route: 'main.adGroups.sources', active: false, hidden: false},
        {heading: 'Settings', route: 'main.adGroups.settings', active: false, hidden: !$scope.hasPermission('dash.settings_view')},
        {heading: 'Agency', route: 'main.adGroups.agency', active: false, hidden: !$scope.hasPermission('zemauth.ad_group_agency_tab_view'), internal: $scope.isPermissionInternal('zemauth.ad_group_agency_tab_view')}
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
        if (!$scope.account || !$scope.campaign || !$scope.adGroup) {
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
    
    $scope.$on('$stateChangeStart', function(event, toState, toParams, fromState, fromParams) {
        $location.search('source_ids', null);
        $location.search('source_totals', null);
        $location.search('page', null);
    });

    $scope.getAdGroupState = function() {
        api.adGroupState.get($state.params.id).then(
            function(data) {
                $scope.setAdGroupPaused(data.state === 2);
            },
            function(){
                // error
            }
        );
    };

    $scope.getModels();
    $scope.updateBreadcrumbAndTitle();
}]);
