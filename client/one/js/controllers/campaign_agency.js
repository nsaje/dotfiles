/*globals oneApp,constants,options,moment*/
oneApp.controller('CampaignAgencyCtrl', ['$scope', '$state', '$modal', 'api', function ($scope, $state, $modal, api) {
    $scope.settings = {};
    $scope.history = [];
    $scope.canArchive = false;
    $scope.canRestore = true;
    $scope.accountManagers = [];
    $scope.salesReps = [];
    $scope.errors = {};
    $scope.availablePixels = [];
    $scope.requestInProgress = false;
    $scope.saved = null;
    $scope.discarded = null;
    $scope.orderField = 'datetime';
    $scope.orderReverse = true;
    $scope.iabCategories = options.iabCategories;

    $scope.getSettings = function (discarded) {
        $scope.saved = null;
        $scope.discarded = null;
        $scope.requestInProgress = true;
        $scope.errors = {};
        api.campaignAgency.get($state.params.id).then(
            function (data) {
                $scope.settings = data.settings;
                $scope.history = data.history;
                $scope.canArchive = data.canArchive;
                $scope.canRestore = data.canRestore;

                if (discarded) {
                    $scope.discarded = true;
                } else {
                    $scope.accountManagers = data.accountManagers;
                    $scope.salesReps = data.salesReps;
                }
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

        api.campaignAgency.save($scope.settings).then(
            function (data) {
                $scope.history = data.history;
                $scope.canArchive = data.canArchive;
                $scope.canRestore = data.canRestore;
                $scope.errors = {};
                $scope.settings = data.settings;
                $scope.updateBreadcrumbAndTitle();
                $scope.requestInProgress = false;
                $scope.saved = true;
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

    $scope.archiveCampaign = function () {
        if ($scope.canArchive) {
            api.campaignArchive.archive($scope.campaign.id).then(function () {
                $scope.refreshPage();
            });
        }
    };

    $scope.restoreCampaign = function () {
        if ($scope.canRestore) {
            api.campaignArchive.restore($scope.campaign.id).then(function () {
                $scope.refreshPage();
            });
        }
    };

    $scope.getSettings();

    $scope.getName = function (user) {
        return user.name;
    };
}]);
