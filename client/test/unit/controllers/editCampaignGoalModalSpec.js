/* global describe,beforeEach,module,it,inject,expect,spyOn */
'use strict';

describe('EditCampaignGoalModalCtrl', function () {
    var $modalInstance, $timeout, $scope, $state, $q, api, openedDeferred;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(function () {
        inject(function ($rootScope, $controller, _$state_, _$q_, _$timeout_) {
            $q = _$q_;
            $timeout = _$timeout_;
            $scope = $rootScope.$new();

            var mockApiFunc = function () {
                return {
                    then: function () {
                        return {
                            finally: function () {},
                        };
                    },
                };
            };

            api = {
                conversionPixel: {
                    post: mockApiFunc,
                },
                campaignGoalValidation: {
                    post: mockApiFunc,
                },
            };

            $state = _$state_;
            $state.params = {id: 1};

            $scope.campaignGoals = [];
            $scope.campaign = {id: 1};
            $scope.account = {id: 1};

            openedDeferred = $q.defer();
            $modalInstance = {
                close: function () {},
                opened: openedDeferred.promise,
            };

            $controller('EditCampaignGoalModalCtrl', {
                $scope: $scope,
                $modalInstance: $modalInstance,
                api: api,
            });
        });
    });

    describe('save', function () {
        it('calls validation and api with goals', function () {
            var deferred = $q.defer();
            $scope.campaignGoal = 'goal';
            $scope.errors = {};

            spyOn(api.campaignGoalValidation, 'post').and.callFake(
                function () {
                    return deferred.promise;
                }
            );
            spyOn($scope, 'validate').and.callFake(
                function () {
                    return true;
                }
            );
            spyOn($modalInstance, 'close');

            $scope.save();

            expect($scope.validate).toHaveBeenCalled();
            expect(api.campaignGoalValidation.post).toHaveBeenCalledWith(1, 'goal');

            $timeout(function () {
                expect($modalInstance.close).toHaveBeenCalled();
            }, 1500);

        });
        it('doesn\'t call api if validation fails', function () {
            var deferred = $q.defer();

            $scope.campaignGoal = 'goal';
            $scope.errors = {};
            spyOn(api.campaignGoalValidation, 'post').and.callFake(
                function () {
                    return deferred.promise;
                }
            );
            spyOn($scope, 'validate').and.callFake(
                function () {
                    return false;
                }
            );
            $scope.save();
            expect($scope.validate).toHaveBeenCalled();
            expect(api.campaignGoalValidation.post).not.toHaveBeenCalled();
        });
    });

    describe('validate', function () {
        it ('catches duplicate conversion goal names', function () {
            var newGoal = {},
                errors = {};
            $scope.campaignGoals = [
                {
                    primary: false,
                    campaignId: 1,
                    id: 1,
                    type: 4,
                    conversionGoal: {
                        goalId: '123', type: 2, name: '123',
                    },
                },
                {
                    primary: true,
                    campaignId: 1,
                    type: 4,
                    conversionGoal: {
                        goalId: '123', type: 3, name: '124',
                    },
                },
            ];

            newGoal = {
                type: 4,
                campaignId: 1,
                conversionGoal: {
                    goalId: 'something', type: 3, name: '124',
                },
            };

            expect($scope.validate(newGoal, errors)).toBe(false);

            newGoal = {
                type: 4,
                campaignId: 1,
                conversionGoal: {
                    goalId: 'something', type: 3, name: '125',
                },
            };

            expect($scope.validate(newGoal, errors)).toBe(true);

        });
        it ('catches duplicate conversion goal ids', function () {
            var newGoal = {},
                errors = {};
            $scope.campaignGoals = [
                {
                    primary: false,
                    campaignId: 1,
                    id: 1,
                    type: 4,
                    conversionGoal: {
                        goalId: '123', type: 2, name: '123',
                    },
                },
                {
                    primary: true,
                    campaignId: 1,
                    type: 4,
                    conversionGoal: {
                        goalId: '123', type: 3, name: '124',
                    },
                },
            ];

            newGoal = {
                type: 4,
                campaignId: 1,
                conversionGoal: {
                    goalId: '123', type: 3, name: '125',
                },
            };

            expect($scope.validate(newGoal, errors)).toBe(false);

            newGoal = {
                type: 4,
                campaignId: 1,
                conversionGoal: {
                    goalId: '124', type: 3, name: '125',
                },
            };

            expect($scope.validate(newGoal, errors)).toBe(true);
        });
        it ('recognizes modified existing goals', function () {
            var newGoal = {},
                errors = {};
            $scope.campaignGoals = [
                {
                    primary: false,
                    campaignId: 1,
                    id: 1,
                    type: 4,
                    conversionGoal: {
                        goalId: '123', type: 2, name: '123',
                    },
                },
                {
                    primary: true,
                    campaignId: 1,
                    type: 4,
                    conversionGoal: {
                        goalId: '123', type: 3, name: '124',
                    },
                },
            ];

            newGoal = {
                type: 4,
                campaignId: 1,
                id: 1,
                conversionGoal: {
                    goalId: '123', type: 2, name: '128',
                },
            };

            expect($scope.validate(newGoal, errors)).toBe(true);
        });

        it ('allows only different conversion windows for same pixie', function () {
            var newGoal = {},
                errors = {};
            $scope.campaignGoals = [
                {
                    primary: false,
                    campaignId: 1,
                    id: 1,
                    type: 4,
                    conversionGoal: {
                        goalId: '123', type: 1, name: '123', conversionWindow: 1,
                    },
                },
                {
                    primary: true,
                    campaignId: 1,
                    type: 4,
                    conversionGoal: {
                        goalId: '123', type: 1, name: '124', conversionWindow: 2,
                    },
                },
            ];

            newGoal = {
                type: 4,
                campaignId: 1,
                conversionGoal: {
                    goalId: '123', type: 1, name: '125', conversionWindow: 2,
                },
            };

            expect($scope.validate(newGoal, errors)).toBe(false);

            newGoal = {
                type: 4,
                campaignId: 1,
                conversionGoal: {
                    goalId: '124', type: 3, name: '125', conversionWindow: 3,
                },
            };

            expect($scope.validate(newGoal, errors)).toBe(true);
        });
    });
});
