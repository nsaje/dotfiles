/*globals oneApp,constants,options,moment*/
oneApp.controller('CampaignSettingsCtrl', ['$scope', '$state', '$q', '$timeout', 'api', function ($scope, $state, $q, $timeout, api) {
    var campaignFreshSettings = $q.defer();
    $scope.settings = {};
    $scope.errors = {};
    $scope.options = options;
    $scope.requestInProgress = false;
    $scope.saved = null;
    $scope.discarded = null;

    $scope.campaignHasFreshSettings = function () {
        return campaignFreshSettings.promise;
    };

    $scope.getSettings = function (discarded) {
        $scope.saved = null;
        $scope.discarded = null;
        $scope.requestInProgress = true;
        $scope.errors = {};
        api.campaignSettings.get($state.params.id).then(
            function (data) {
                $scope.settings = data.settings;
                $scope.discarded = discarded;
                campaignFreshSettings.resolve(data.settings.name === 'New campaign');
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.requestInProgress = false;
        });
    };

    $scope.saveSettings = function () {
        $scope.saved = null;
        $scope.discarded = null;
        $scope.requestInProgress = true;

        api.campaignSettings.save($scope.settings).then(
            function (data) {
                $scope.errors = {};
                $scope.settings = data.settings;
                $scope.updateAccounts(data.settings.name);
                $scope.updateBreadcrumbAndTitle();
                $scope.requestInProgress = false;
                $scope.saved = true;

                if ($scope.user.automaticallyCreateAdGroup && $scope.user.showOnboardingGuidance) {
                    $scope.user.automaticallyCreateAdGroup = false;
                    api.campaignAdGroups.create($scope.campaign.id).then(function (adGroupData) {

                        $scope.campaign.adGroups.push({
                            id: adGroupData.id,
                            name: adGroupData.name,
                            contentAdsTabWithCMS: data.contentAdsTabWithCMS,
                            status: 'stopped',
                            state: 'paused'
                        });
                        $timeout(function () {
                            $state.go('main.adGroups.settings', {id: adGroupData.id});
                        }, 100);
                    });
                }
            },
            function (data) {
                $scope.errors = data;
                $scope.saved = false;
            }
        ).finally(function () {
            $scope.requestInProgress = false;
        });
    };

    $scope.refreshPage = function () {
        api.navData.list().then(function (accounts) {
            $scope.refreshNavData(accounts);
            $scope.getModels();
        });
        $scope.getSettings();
    };

    $scope.getSettings();
}]);
