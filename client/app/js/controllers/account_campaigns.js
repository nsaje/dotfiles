/*globals oneApp*/
oneApp.controller('AccountCampaignsCtrl', ['$scope', '$state', 'api', function ($scope, $state, api) {
    $scope.requestInProgress = false;
    $scope.addedName = null;
    $scope.added = null;

    $scope.addCampaign = function () {
        var accountId = $state.params.id;
        $scope.requestInProgress = true;
        $scope.addedName = null;
        $scope.added = null;

        api.accountCampaigns.create(accountId).then(
            function (data) {
                $scope.accounts.forEach(function (account) {
                    if (account.id.toString() === accountId.toString()) {
                        account.campaigns.push({
                            id: data.id,
                            name: data.name,
                            adGroups: []
                        });

                        $scope.addedName = data.name;
                        $scope.added = true;
                    }
                });
            },
            function (data) {
                // error
                $scope.added = false;
            }
        ).finally(function () {
            $scope.requestInProgress = false;
        });
    };
}]);
