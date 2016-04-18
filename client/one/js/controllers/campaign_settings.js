/* globals oneApp,constants,options */
oneApp.controller('CampaignSettingsCtrl', ['$scope', '$state', '$q', '$timeout', 'api', 'zemNavigationService', function ($scope, $state, $q, $timeout, api, zemNavigationService) { // eslint-disable-line max-len
    var campaignFreshSettings = $q.defer();
    $scope.settings = {};
    $scope.errors = {};
    $scope.options = options;
    $scope.requestInProgress = false;
    $scope.saved = null;
    $scope.discarded = null;
    $scope.campaignGoals = [],
    $scope.campaignGoalsDiff = {};

    function validateGoals () {
        var primary = false,
            goals = $scope.campaignGoals;
        if (!goals || !goals.length) {
            return true;
        }
        goals.forEach(function (goal) {
            if (goal.primary) {
                primary = true;
            }
        });
        if (!primary) {
            $scope.errors.goals = ['One goal has to be set as primary.'];
        }
        return primary;
    }

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
                $scope.campaignGoals = data.goals;

                $scope.discarded = discarded;
                campaignFreshSettings.resolve(data.settings.name === 'New campaign');
            },
            function () {
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

        if (!validateGoals()) {
            return;
        }

        $scope.requestInProgress = true;

        api.campaignSettings.save($scope.settings, $scope.campaignGoalsDiff).then(
            function (data) {
                $scope.errors = {};
                $scope.settings = data.settings;

                if (data.goals) {
                    $scope.campaignGoals.length = 0;
                    Array.prototype.push.apply($scope.campaignGoals, data.goals);
                }

                zemNavigationService.updateCampaignCache(
                    $scope.campaign.id, {name: data.settings.name}
                );

                $scope.requestInProgress = false;
                $scope.saved = true;

                if ($scope.user.automaticallyCreateAdGroup && $scope.user.showOnboardingGuidance) {
                    $scope.user.automaticallyCreateAdGroup = false;
                    api.campaignAdGroups.create($scope.campaign.id).then(function (adGroupData) {
                        zemNavigationService.addAdGroupToCache($scope.campaign.id, {
                            id: adGroupData.id,
                            name: adGroupData.name,
                            contentAdsTabWithCMS: data.contentAdsTabWithCMS,
                            status: constants.adGroupSettingsState.INACTIVE,
                            state: constants.adGroupRunningStatus.INACTIVE,
                        });
                        $timeout(function () {
                            $state.go('main.adGroups.settings', {id: adGroupData.id});
                        }, 100);
                    });
                }

                $scope.campaignGoalsDiff.added = [];
                $scope.campaignGoalsDiff.removed = [];
                $scope.campaignGoalsDiff.primary = null;
                $scope.campaignGoalsDiff.modified = {};
            },
            function (data) {
                $scope.errors = data;
                $scope.saved = false;
            }
        ).finally(function () {
            $scope.requestInProgress = false;
        });
    };

    $scope.getSettings();
    $scope.setActiveTab();
}]);
