/*globals oneApp,$,moment*/
oneApp.controller('CampaignCtrl', ['$scope', '$state', function ($scope, $state) {
    $scope.tabs = [
        {heading: 'Agency', route: 'main.campaigns.agency', active: true, hidden: !$scope.hasPermission('dash.settings_view')}
    ];

    $scope.updateBreadcrumbAndTitle = function () {
        if (!$scope.accounts) {
            return;
        }

        $scope.accounts.forEach(function (account) {
            account.campaigns.forEach(function (campaign) {
                    if (campaign.id.toString() === $state.params.id) {
                        $scope.$parent.setBreadcrumbAndTitle(
                            [account.name, campaign.name],
                            campaign.name
                        );
                    }
            });
        });
    };

    $scope.tabs.forEach(function(tab) {
        tab.active = $state.is(tab.route);
    });

    $scope.updateBreadcrumbAndTitle();
}]);
