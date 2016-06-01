/* globals oneApp, options */
oneApp.controller('CampaignAgencyCtrl', ['$scope', '$state', '$modal', 'api', 'zemNavigationService', function ($scope, $state, $modal, api, zemNavigationService) { // eslint-disable-line max-len
    $scope.settings = {};
    $scope.history = [];
    $scope.campaignManagers = [];
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

                if (discarded) {
                    $scope.discarded = true;
                } else {
                    $scope.campaignManagers = data.campaignManagers;
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
        zemNavigationService.reload();
        $scope.getSettings();
    };

    $scope.getSettings();

    $scope.getName = function (user) {
        return user.name;
    };
}]);
