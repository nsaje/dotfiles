/*globals oneApp*/
oneApp.controller('AccountCampaignsCtrl', ['$scope', '$state', 'api', function ($scope, $state, api) {
    $scope.requestInProgress = false;

    $scope.addCampaign = function () {
        var accountId = $state.params.id;
        $scope.requestInProgress = true;

        api.accountCampaigns.create(accountId).then(
            function (data) {
                $scope.accounts.forEach(function (account) {
                    if (account.id.toString() === accountId.toString()) {
                        account.campaigns.push({
                            id: data.id,
                            name: data.name,
                            adGroups: []
                        });

                        $state.go('main.campaigns.agency', {id: data.id});
                    }
                });
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.requestInProgress = false;
        });
    };
}]);
