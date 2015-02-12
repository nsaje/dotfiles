/*globals oneApp,$,moment*/
oneApp.controller('AdGroupCtrl', ['$scope', '$state', '$location', 'api', function ($scope, $state, $location, api) {
    $scope.level = constants.level.AD_GROUPS;
    $scope.getTabs = function() {
        return [{
            heading: 'Content Ads',
            route: 'main.adGroups.ads',
            active: true,
            hidden: ($scope.hasPermission('zemauth.view_archived_entities') && $scope.adGroup && $scope.adGroup.archived)
        }, {
            heading: 'Media Sources',
            route: 'main.adGroups.sources',
            active: false,
            hidden: ($scope.hasPermission('zemauth.view_archived_entities') && $scope.adGroup && $scope.adGroup.archived)
        }, {
            heading: 'Settings',
            route: 'main.adGroups.settings',
            active: false,
            hidden: (!$scope.hasPermission('dash.settings_view') && !$scope.hasPermission('zemauth.view_archived_entities')) || (!$scope.hasPermission('dash.settings_view') && !($scope.adGroup && $scope.adGroup.archived)) || ($scope.hasPermission('zemauth.ad_group_agency_tab_view') && $scope.hasPermission('zemauth.view_archived_entities') && ($scope.adGroup && $scope.adGroup.archived))
        }, {
            heading: 'Agency',
            route: 'main.adGroups.agency',
            active: false,
            hidden: !$scope.hasPermission('zemauth.ad_group_agency_tab_view'),
            internal: $scope.isPermissionInternal('zemauth.ad_group_agency_tab_view')
        }, {
            heading: 'Content Ads+',
            route: 'main.adGroups.adsPlus',
            active: false,
            hidden: !$scope.hasPermission('zemauth.new_content_ads_tab') || ($scope.hasPermission('zemauth.view_archived_entities') && $scope.adGroup && $scope.adGroup.archived),
            internal: $scope.isPermissionInternal('zemauth.new_content_ads_tab')
        }];
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
        $scope.setBreadcrumbAndTitle([{
                name: $scope.account.name,
                state: $scope.getDefaultAccountState(),
                params: {id: $scope.account.id},
                disabled: !$scope.canAccessAccounts()
            }, {
                name: $scope.campaign.name,
                state: $scope.getDefaultCampaignState(),
                params: {id: $scope.campaign.id},
                disabled: !$scope.canAccessCampaigns()
            }, {
                name: $scope.adGroup.name,
                state: $scope.getDefaultAdGroupState(),
                params: {id: $scope.adGroup.id},
                disabled: true
            }],
            $scope.adGroup.name + ' - ' + $scope.campaign.name
        );
    };

    $scope.$on('$stateChangeStart', function(event, toState, toParams, fromState, fromParams) {
        $location.search('source_ids', null);
        $location.search('source_totals', null);
        $location.search('page', null);
    });

    $scope.$on('$stateChangeSuccess', function () {
        $scope.updateBreadcrumbAndTitle();
    });

    $scope.getAdGroupState = function() {
        api.adGroupState.get($state.params.id).then(
            function(data) {
                $scope.setAdGroupPaused(data.state === 2 && !$scope.adGroup.archived);
            },
            function(){
                // error
            }
        );
    };

    $scope.getModels();
    $scope.tabs = $scope.getTabs();
    $scope.setActiveTab();

    if ($scope.hasPermission('zemauth.view_archived_entities') && $scope.adGroup && $scope.adGroup.archived) {
        if ($scope.hasPermission('zemauth.ad_group_agency_tab_view')) {
            $state.go('main.adGroups.agency', {id: $scope.adGroup.id});
        } else {
            $state.go('main.adGroups.settings', {id: $scope.adGroup.id});
        }
    }

    $scope.$watch('adGroup.archived', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.tabs = $scope.getTabs();
            $scope.setActiveTab();
        }
    });
}]);
