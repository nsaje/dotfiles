/*globals oneApp,$,moment*/
oneApp.controller('CampaignCtrl', ['$scope', '$state', function ($scope, $state) {
    $scope.tabs = [
        {heading: 'Ad groups', route: 'main.campaigns.ad_groups', active: true, hidden: !$scope.hasPermission('zemauth.campaign_ad_groups_view'), internal: $scope.isPermissionInternal('zemauth.campaign_ad_groups_view')},
        {heading: 'Agency', route: 'main.campaigns.agency', active: false, hidden: !$scope.hasPermission('zemauth.campaign_settings_view'), internal: $scope.isPermissionInternal('zemauth.campaign_settings_view')}
    ];

    $scope.account = null;
    $scope.campaign = null;

    $scope.getModels = function () {
        $scope.accounts.forEach(function (account) {
            account.campaigns.forEach(function (campaign) {
                if (campaign.id.toString() === $state.params.id) {
                    $scope.account = account;
                    $scope.campaign = campaign;
                }
            });
        });
    };

    $scope.updateBreadcrumbAndTitle = function () {
        if (!$scope.accounts) {
            return;
        }
        $scope.setBreadcrumbAndTitle(
            [{name: $scope.account.name, state: $scope.getDefaultAccountState() + '({id: ' + $scope.account.id + '})', disabled: !$scope.canAccessAccounts()},
            {name: $scope.campaign.name, state: $scope.getDefaultCampaignState() + '({id: ' + $scope.campaign.id + '})', disabled: true}],
            $scope.campaign.name
        );
    };

    $scope.updateAccounts = function (newCampaignName) {
        if (!$scope.accounts || !newCampaignName) {
            return;
        }
        $scope.campaign.name = newCampaignName;
    };

    $scope.tabs.forEach(function(tab) {
        tab.active = $state.is(tab.route);
    });

    $scope.getModels();
    $scope.updateBreadcrumbAndTitle();
}]);
