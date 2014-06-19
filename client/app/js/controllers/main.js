/*globals oneApp*/
oneApp.controller('MainCtrl', ['$scope', '$state', 'api', function ($scope, $state, api) {
    $scope.tabs = [
        {heading: 'Ads', route: 'adGroups.ads', active: true},
        {heading: 'Networks', route: 'adGroups.networks', active: false},
        {heading: 'Settings', route: 'adGroups.settings', active: false}
    ];
    $scope.accounts = [];

    $scope.breadcrumb = [];
    
    $scope.$on("$stateChangeSuccess", function() {
        $scope.tabs.forEach(function(tab) {
            tab.active = $state.is(tab.route);
        });
    });

    api.navData.list().then(function (data) {
        $scope.accounts = data;
    });

    $scope.$watch('accounts', function (newValue, oldValue) {
        $scope.accounts.forEach(function (account) {
            account.campaigns.forEach(function (campaign) {
                campaign.adGroups.forEach(function (adGroup) {
                    if (adGroup.id.toString() === $state.params.id) {
                        $scope.breadcrumb = [account.name, campaign.name, adGroup.name];
                    }
                });
            });
        });
    });
}]);
