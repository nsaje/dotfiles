/*globals oneApp*/
oneApp.controller('CampaignAdGroupsCtrl', ['$scope', '$state', 'api', function ($scope, $state, api) {
    $scope.requestInProgress = false;
    $scope.addedName = null;
    $scope.added = null;

    $scope.addAdGroup = function () {
        var campaignId = $state.params.id;
        $scope.requestInProgress = true;
        $scope.addedName = null;
        $scope.added = null;

        api.campaignAdGroups.create(campaignId).then(
            function (data) {
                $scope.accounts.forEach(function (account) {
                    account.campaigns.forEach(function (campaign) {
                        if (campaign.id.toString() === campaignId.toString()) {
                            campaign.adGroups.push({
                                id: data.id,
                                name: data.name
                            });

                            $scope.addedName = data.name;
                            $scope.added = true;
                        }
                    });
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
