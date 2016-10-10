/* globals angular, constants, options */
angular.module('one.legacy').controller('CampaignSettingsCtrl', ['$scope', '$state', '$q', '$timeout', 'api', 'zemCampaignService', 'zemNavigationService', function ($scope, $state, $q, $timeout, api, zemCampaignService, zemNavigationService) { // eslint-disable-line max-len
    var campaignFreshSettings = $q.defer();
    $scope.settings = {};
    $scope.errors = {};
    $scope.constants = constants;
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
        zemCampaignService.get($state.params.id).then(
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

        var updateData = {
            settings: $scope.settings,
            goals: $scope.campaignGoalsDiff
        };
        zemCampaignService.update($scope.settings.id, updateData).then(
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
            zemCampaignService.archive($scope.campaign.id).then(function () {
                $scope.requestInProgress = false;
                $scope.refreshPage();
            }, function () {
                $scope.requestInProgress = false;
            });
        }
    };

    $scope.restoreCampaign = function () {
        if ($scope.canRestore) {
            $scope.requestInProgress = true;
            zemCampaignService.restore($scope.campaign.id).then(function () {
                $scope.requestInProgress = false;
                $scope.refreshPage();
            }, function () {
                $scope.requestInProgress = false;
            });
        }
    };

    $scope.refreshPage = function () {
        $scope.getSettings();
        zemNavigationService.reload();
    };

    $scope.getGaTrackingTypeByValue = function (value) {
        var result;
        for (var i = 0; i < options.gaTrackingType.length; i++) {
            var type = options.gaTrackingType[i];
            if (type.value === value) {
                result = type;
                break;
            }
        }
        return result;
    };

    $scope.getSettings();
    $scope.setActiveTab();
}]);
