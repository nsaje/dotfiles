/*globals oneApp*/
oneApp.controller('CampaignAdGroupsCtrl', ['$scope', '$state', 'api', function ($scope, $state, api) {
    $scope.requestInProgress = false;

    $scope.addAdGroup = function () {
        var campaignId = $state.params.id;
        $scope.requestInProgress = true;

        api.campaignAdGroups.create(campaignId).then(
            function (data) {
                $scope.accounts.forEach(function (account) {
                    account.campaigns.forEach(function (campaign) {
                        if (campaign.id.toString() === campaignId.toString()) {
                            campaign.adGroups.push({
                                id: data.id,
                                name: data.name
                            });

                            $state.go('main.adGroups.settings', {id: data.id});
                        }
                    });
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
