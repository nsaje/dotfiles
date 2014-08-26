/*globals oneApp*/
oneApp.controller('AccountCampaignsCtrl', ['$scope', '$state', 'api', function ($scope, $state, api) {
    $scope.addCampaign = function () {
        var accountId = $state.params.id;
        api.accountCampaigns.create(accountId).then(
            function (data) {
                $scope.accounts.forEach(function (account) {
                    if (account.id.toString() === accountId.toString()) {
                        account.campaigns.push({
                            id: data.id,
                            name: data.name,
                            adGroups: []
                        });
                    }
                });
            },
            function (data) {
                // error
                return;
            }
        );
    };
}]);
