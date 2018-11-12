//
// TODO: On major update, refactor to component
//
angular
    .module('one.widgets')
    .controller('zemEditCampaignGoalModalCtrl', function(
        $scope,
        zemConversionPixelsEndpoint,
        zemCampaignGoalValidationEndpoint,
        zemNavigationNewService,
        zemMulticurrencyService,
        zemPermissions
    ) {
        // eslint-disable-line max-len
        $scope.addConversionGoalInProgress = false;
        $scope.error = false;
        $scope.newCampaignGoal = false;
        $scope.pixels = {};
        $scope.newPixel = {};
        $scope.savingInProgress = false;

        var activeAccount = zemNavigationNewService.getActiveAccount();

        var MAX_CONVERSION_GOALS = 15;

        if ($scope.campaignGoal === undefined) {
            $scope.newCampaignGoal = true;
            $scope.campaignGoal = {
                primary: false,
            };
        } else {
            $scope.prevValue = $scope.campaignGoal.value;
        }

        $scope.errors = {
            conversionGoal: {},
        };

        function getTypeId(goal) {
            if (
                goal.conversionGoal &&
                goal.conversionGoal.type !== constants.conversionGoalType.PIXEL
            ) {
                return (
                    goal.conversionGoal.type + '::' + goal.conversionGoal.goalId
                );
            }
            return [
                goal.conversionGoal.type,
                goal.conversionGoal.goalId,
                goal.conversionGoal.conversionWindow,
            ].join('::');
        }

        /* eslint-disable complexity */
        function isGoalAvailable(option) {
            var isAvailable = true,
                goal = $scope.campaignGoal,
                isCpcGoal = option.value === constants.campaignGoalKPI.CPC,
                countConversionGoals = 0;

            if (!goal || (goal && goal.type === option.value)) {
                return true;
            }
            if (
                (zemPermissions.hasPermission('zemauth.disable_public_rcs') ||
                    zemPermissions.hasPermission(
                        'zemauth.disable_public_newscorp'
                    )) &&
                !isCpcGoal
            ) {
                return false;
            }

            $scope.campaignGoals.forEach(function(goal) {
                if (goal.type === option.value) {
                    isAvailable = false;
                }
                countConversionGoals +=
                    goal.type === constants.campaignGoalKPI.CPA;
            });

            if (
                option.value === constants.campaignGoalKPI.CPA &&
                countConversionGoals < MAX_CONVERSION_GOALS
            ) {
                return true;
            }

            // Display campaigns do not support CPCV goals
            if (
                parseInt($scope.campaign.type) ===
                    constants.campaignTypes.DISPLAY &&
                option.value === constants.campaignGoalKPI.CPCV
            ) {
                return false;
            }

            return isAvailable;
        }

        $scope.validate = function(newGoal, allErrors) {
            var goalTypeIds = {},
                errors = {};

            if (!$scope.newCampaignGoal) {
                return true;
            }

            if (newGoal.type !== constants.campaignGoalKPI.CPA) {
                return true;
            }

            goalTypeIds[getTypeId(newGoal)] = 1;

            $scope.campaignGoals.forEach(function(goal) {
                if (goal.type !== constants.campaignGoalKPI.CPA) {
                    return;
                }
                if (newGoal.id && newGoal.id === goal.id) {
                    // skip same rows
                    return;
                }
                var typeId = getTypeId(goal);
                if (!goalTypeIds[typeId]) {
                    goalTypeIds[typeId] = 0;
                }

                goalTypeIds[typeId]++;
            });

            angular.forEach(goalTypeIds, function(count) {
                if (count > 1) {
                    errors.goalId = ['This field has to be unique'];
                }
            });
            if (errors.goalId) {
                allErrors.conversionGoal = errors;
                return false;
            }
            return true;
        };

        $scope.cancel = function() {
            $scope.campaignGoal.value = $scope.prevValue;
            $scope.$dismiss();
        };

        $scope.save = function() {
            $scope.savingInProgress = true;
            $scope.errors = {};

            $scope.campaignGoal.value = Math.abs($scope.campaignGoal.value);

            if (!$scope.newCampaignGoal) {
                $scope.$close($scope.campaignGoal);
                $scope.savingInProgress = false;
                return; // Skip server validation call if this is not a new entry
            }

            if (!$scope.validate($scope.campaignGoal, $scope.errors)) {
                $scope.savingInProgress = false;
                return;
            }

            if (
                $scope.campaignGoal.conversionGoal &&
                $scope.campaignGoal.conversionGoal.type ===
                    constants.conversionGoalType.PIXEL &&
                $scope.campaignGoal.conversionGoal.goalId === '___new___'
            ) {
                zemConversionPixelsEndpoint
                    .post($scope.account.id, $scope.newPixel)
                    .then(
                        function(data) {
                            $scope.campaignGoal.conversionGoal.goalId = data.id;
                            $scope.campaignGoal.conversionGoal.pixelUrl =
                                data.url;

                            saveApi($scope.campaign.id, $scope.campaignGoal);
                        },
                        function(data) {
                            if (data && data.message) {
                                $scope.errors.conversionGoal = {
                                    pixel: [data.message],
                                };
                            }
                            $scope.savingInProgress = false;
                        }
                    );
            } else {
                saveApi($scope.campaign.id, $scope.campaignGoal);
            }
        };

        function saveApi(campaignId, campaignGoal) {
            zemCampaignGoalValidationEndpoint
                .post(campaignId, campaignGoal)
                .then(
                    function(goal) {
                        campaignGoal.conversionGoal = goal.conversionGoal;
                        $scope.$close(campaignGoal);
                        $scope.savingInProgress = false;
                    },
                    function(errors) {
                        $scope.errors = errors;
                        $scope.savingInProgress = false;
                    }
                );
        }

        $scope.showAddConversionGoalForm = function() {
            return $scope.campaignGoal.type === constants.campaignGoalKPI.CPA;
        };

        $scope.campaignGoalKPIs = angular
            .copy(options.campaignGoalKPIs)
            .filter(isGoalAvailable)
            .map(function(goalKPI) {
                if (goalKPI.unit === '__CURRENCY__') {
                    goalKPI.unit = zemMulticurrencyService.getAppropriateCurrencySymbol(
                        activeAccount
                    );
                }
                return goalKPI;
            });

        function filterPixels(pixels) {
            var availablePixels = [];
            pixels.forEach(function(p) {
                var counts = {},
                    invalid = 0;
                if (p.archived) {
                    return;
                }
                $scope.campaignGoals.forEach(function(goal) {
                    if (goal.type !== constants.campaignGoalKPI.CPA) {
                        return;
                    }
                    if (goal.conversionGoal.goalId === p.id) {
                        if (!counts[goal.conversionGoal.conversionWindow]) {
                            counts[goal.conversionGoal.conversionWindow] = 0;
                        }
                        counts[goal.conversionGoal.conversionWindow]++;
                    }
                });
                options.conversionWindows.forEach(function(opt) {
                    if (counts[opt.value]) {
                        invalid += 1;
                    }
                });
                if (invalid < options.conversionWindows.length) {
                    availablePixels.push(p);
                }
            });
            availablePixels.push({
                id: '___new___',
                name: 'Create new pixel',
            });
            return availablePixels;
        }

        function getPixelsWithAvailableConversionWindows(pixels) {
            var pixelsWithAvailableConversionWindows = [];
            pixels.forEach(function(pixel) {
                pixel = angular.copy(pixel);
                pixel.conversionWindows = [];

                var counts = {};
                $scope.campaignGoals.forEach(function(goal) {
                    if (goal.type !== constants.campaignGoalKPI.CPA) {
                        return;
                    }
                    if (goal.conversionGoal.goalId === pixel.id) {
                        if (!counts[goal.conversionGoal.conversionWindow]) {
                            counts[goal.conversionGoal.conversionWindow] = 0;
                        }
                        counts[goal.conversionGoal.conversionWindow]++;
                    }
                });
                options.conversionWindows.forEach(function(conversionWindow) {
                    if (!counts[conversionWindow.value]) {
                        pixel.conversionWindows.push(conversionWindow);
                    }
                });
                pixelsWithAvailableConversionWindows.push(pixel);
            });
            return pixelsWithAvailableConversionWindows;
        }

        $scope.pixels.loading = true;
        zemConversionPixelsEndpoint
            .list($scope.account.id)
            .then(function(data) {
                var availablePixels = filterPixels(data.rows);
                $scope.pixels.list = getPixelsWithAvailableConversionWindows(
                    availablePixels
                );
                $scope.pixels.loading = false;
            });
    });

angular
    .module('one.widgets')
    .service('zemCampaignGoalValidationEndpoint', function($q, $http) {
        this.post = post;

        function post(campaignId, goal) {
            var url = '/api/campaigns/' + campaignId + '/goals/validate/';
            var deferred = $q.defer();

            $http
                .post(url, convert.dataToApi(goal))
                .success(function(data) {
                    deferred.resolve(convert.dataFromApi(data));
                })
                .error(function(data) {
                    deferred.reject(convert.errorsFromApi(data));
                });

            return deferred.promise;
        }

        var convert = {
            dataToApi: function(goal) {
                var data = {
                    type: goal.type,
                    value: goal.value,
                    id: goal.id,
                };
                if (goal.conversionGoal) {
                    data.conversion_goal = {
                        goal_id: goal.conversionGoal.goalId,
                        name: goal.conversionGoal.name,
                        type: goal.conversionGoal.type,
                        conversion_window: goal.conversionGoal.conversionWindow,
                    };
                }
                return data;
            },
            dataFromApi: function(data) {
                var goal = data.data;

                if (goal && goal.conversion_goal) {
                    return {
                        conversionGoal: {
                            name: goal.conversion_goal.name,
                            type: goal.conversion_goal.type,
                            conversionWindow:
                                goal.conversion_goal.conversion_window,
                            goalId: goal.conversion_goal.goal_id,
                        },
                    };
                }

                return {};
            },
            errorsFromApi: function(data) {
                var result = {};
                var errors = data.data.errors;

                if (errors.conversion_goal) {
                    result.conversionGoal = {
                        goalId: errors.conversion_goal.goal_id,
                        name: errors.conversion_goal.name,
                        type: errors.conversion_goal.type,
                        conversionWindow:
                            errors.conversion_goal.conversion_window,
                    };
                }
                return result;
            },
        };
    });
