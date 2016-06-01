/* globals oneApp,options */
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
    $scope.canArchive = false;
    $scope.canRestore = false;
    $scope.iabCategories = options.iabCategories;

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

    $scope.getSettings = function (discarded) {
        $scope.saved = null;
        $scope.discarded = null;
        $scope.requestInProgress = true;
        $scope.errors = {};
        api.campaignSettings.get($state.params.id).then(
            function (data) {
                $scope.settings = data.settings;
                $scope.campaignGoals = data.goals;
                $scope.canArchive = data.canArchive;
                $scope.canRestore = data.canRestore;

                $scope.discarded = discarded;
                if (discarded) {
                    $scope.discarded = true;
                } else {
                    $scope.campaignManagers = data.campaignManagers;
                }
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

    $scope.archiveCampaign = function () {
        if ($scope.canArchive) {
            $scope.requestInProgress = true;
            api.campaignArchive.archive($scope.campaign.id).then(function () {
                $scope.refreshPage();
            }, function () {
                $scope.requestInProgress = false;
            });
        }
    };

    $scope.restoreCampaign = function () {
        if ($scope.canRestore) {
            $scope.requestInProgress = true;
            api.campaignArchive.restore($scope.campaign.id).then(function () {
                $scope.refreshPage();
            }, function () {
                $scope.requestInProgress = false;
            });
        }
    };

    $scope.refreshPage = function () {
        zemNavigationService.reload();
        $scope.getSettings();
    };


    $scope.refreshPage();
    $scope.setActiveTab();
}]);
