/*globals oneApp,$,moment*/
oneApp.controller('AdGroupCtrl', ['$scope', '$state', '$location', 'api', function ($scope, $state, $location, api) {
    $scope.level = constants.level.AD_GROUPS;
    $scope.getTabs = function() {
        return [
            {heading: 'Content Ads', route: 'main.adGroups.ads', active: true, hidden: ($scope.adGroup && $scope.adGroup.archived)},
            {heading: 'Media Sources', route: 'main.adGroups.sources', active: false, hidden: ($scope.adGroup && $scope.adGroup.archived)},
            {heading: 'Settings', route: 'main.adGroups.settings', active: false, hidden: !$scope.hasPermission('dash.settings_view') || ($scope.adGroup && $scope.adGroup.archived)},
            {heading: 'Agency', route: 'main.adGroups.agency', active: false, hidden: !$scope.hasPermission('zemauth.ad_group_agency_tab_view'), internal: $scope.isPermissionInternal('zemauth.ad_group_agency_tab_view')}
        ];
    };
    $scope.setActiveTab = function () {
        $scope.tabs.forEach(function(tab) {
            tab.active = $state.is(tab.route);
        });
    };

    $scope.isAdGroupPaused = false;

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
                        $scope.setAccount(account);
                        $scope.setCampaign(campaign);
                        $scope.setAdGroup(adGroup);
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
            [{name: $scope.account.name, state: $scope.getDefaultAccountState() + '({id: ' + $scope.account.id + '})', disabled: !$scope.canAccessAccounts()},
            {name: $scope.campaign.name, state: $scope.getDefaultCampaignState() + '({id: ' + $scope.campaign.id + '})', disabled: !$scope.canAccessCampaigns()},
            {name: $scope.adGroup.name, state: $scope.getDefaultAdGroupState() + '({id: ' + $scope.adGroup.id + '})', disabled: true}],
            $scope.adGroup.name + ' - ' + $scope.campaign.name
        );
    };

    $scope.$on('$stateChangeStart', function(event, toState, toParams, fromState, fromParams) {
        $location.search('source_ids', null);
        $location.search('source_totals', null);
        $location.search('page', null);
        $location.search('size', null);
        $location.search('chart_metric1', null);
        $location.search('chart_metric2', null);
        $location.search('order', null);
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
    $scope.tabs = $scope.getTabs();
    $scope.setActiveTab();

    if ($scope.adGroup && $scope.adGroup.archived && !$state.is('main.adGroups.agency')) {
        $state.go('main.adGroups.agency', {id: $scope.adGroup.id});
    } else if ($scope.campaign && $scope.campaign.archived && !$state.is('main.campaigns.agency')) {
        $state.go('main.campaigns.agency', {id: $scope.campaign.id});
    } else if ($scope.account && $scope.account.archived && !$state.is('main.accounts.agency')) {
        $state.go('main.accounts.agency', {id: $scope.account.id});
    }

    $scope.updateBreadcrumbAndTitle();

    $scope.$watch('adGroup.archived', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.tabs = $scope.getTabs();
            $scope.setActiveTab();
        }
    });
}]);
