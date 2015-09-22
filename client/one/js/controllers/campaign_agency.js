/*globals oneApp,constants,options,moment*/
oneApp.controller('CampaignAgencyCtrl', ['$scope', '$state', '$modal', 'api', function ($scope, $state, $modal, api) {
    $scope.constants = constants;
    $scope.settings = {};
    $scope.history = [];
    $scope.canArchive = false;
    $scope.canRestore = true;
    $scope.accountManagers = [];
    $scope.salesReps = [];
    $scope.errors = {};
    $scope.conversionGoals = [];
    $scope.availablePixels = [];
    $scope.requestInProgress = false;
    $scope.goalsRequestInProgress = false;
    $scope.goalsError = false;
    $scope.removeConversionGoalInProgress = false;
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

    $scope.getConversionPixelTag = function (url) {
        return '<img src="' + url + '" height="1" width="1" border="0" alt="" />';
    };

    function constructConversionGoalRow (row) {
        var ret = {
            id: row.id,
            rows: [
                {title: 'Name', value: row.name},
                {title: 'Type', value: $scope.getConversionGoalType(row)}
            ]
        };

        if (row.type === constants.conversionGoalType.PIXEL) {
            ret.rows.push(
                {title: 'Conversion window', value: $scope.getConversionWindowText(row)},
                {title: 'Pixel URL',
                 value: row.pixel.url,
                 link:
                 {
                     text: 'COPY TAG',
                     click: function () {
                        var scope = $scope.$new(true);
                        scope.conversionPixelTag = $scope.getConversionPixelTag(row.pixel.url);

                        var modalInstance = $modal.open({
                            templateUrl: '/partials/copy_conversion_pixel_modal.html',
                            windowClass: 'modal',
                            scope: scope
                        });

                        return modalInstance;
                     }
                 }
                }
            );
        } else if (row.type === constants.conversionGoalType.GA) {
            ret.rows.push(
                {title: 'Goal number', value: row.goalId}
            );
        } else if (row.type === constants.conversionGoalType.OMNITURE) {
            ret.rows.push(
                {title: 'Event number', value: row.goalId}
            );
        }

        return ret;
    };

    $scope.getConversionGoals = function () {
        $scope.goalsRequestInProgress = true;
        api.conversionGoal.list($scope.campaign.id).then(
            function (data) {
                $scope.conversionGoals = data.rows.map(constructConversionGoalRow);
                $scope.availablePixels = data.availablePixels;
            },
            function () {
                $scope.goalsError = true;
            }
        ).finally(function () {
            $scope.goalsRequestInProgress = false;
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

    $scope.addConversionGoal = function () {
        var modalInstance = $modal.open({
            templateUrl: '/partials/add_conversion_goal_modal.html',
            controller: 'AddConversionGoalModalCtrl',
            windowClass: 'modal',
            scope: $scope
        });

        modalInstance.result.then(function() {
            $scope.getConversionGoals();
            $scope.getSettings();
        });

        return modalInstance;
    };

    $scope.removeConversionGoal = function (id) {
        $scope.removeConversionGoalInProgress = true;
        api.conversionGoal.delete(id).then(
            function () {
                $scope.conversionGoals = $scope.conversionGoals.filter(function (conversionGoalRow) {
                    if (conversionGoalRow.id === id) {
                        return false;
                    }

                    return true;
                });
            },
            function () {
                $scope.goalsError = true;
            }
         ).finally(function() {
            $scope.removeConversionGoalInProgress = false;
        });
    };

    $scope.getConversionGoalType = function (goal) {
        if (goal.type === 1) {
            return 'Conversion Pixel';
        } else if (goal.type === 2) {
            return 'Google Analytics';
        } else if (goal.type === 3) {
            return 'Omniture Event';
        }

        return '';
    };

    $scope.getConversionWindowText = function (goal) {
        if (goal.conversionWindow === 1) {
            return '1 day';
        } else if (goal.conversionWindow === 7) {
            return '7 days';
        } else if (goal.conversionWindow === 30) {
            return '30 days';
        }

        return '';
    };

    $scope.getSettings();
    $scope.getConversionGoals();

    $scope.getName = function (user) {
        return user.name;
    };
}]);
