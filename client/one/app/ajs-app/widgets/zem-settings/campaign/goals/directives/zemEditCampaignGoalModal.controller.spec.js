describe('zemEditCampaignGoalModalCtrl', function() {
    var $timeout, $scope, $state, $q, api;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(angular.mock.module('stateMock'));

    beforeEach(function() {
        inject(function($rootScope, $controller, _$state_, _$q_, _$timeout_) {
            $q = _$q_;
            $timeout = _$timeout_;
            $scope = $rootScope.$new();
            $scope.$close = function() {};

            var mockApiFunc = function() {
                return {
                    then: function() {
                        return {
                            finally: function() {},
                        };
                    },
                };
            };

            api = {
                conversionPixel: {
                    post: mockApiFunc,
                    list: mockApiFunc,
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

            $controller('zemEditCampaignGoalModalCtrl', {
                $scope: $scope,
                zemConversionPixelsEndpoint: api.conversionPixel,
                zemCampaignGoalValidationEndpoint: api.campaignGoalValidation,
            });
        });
    });

    describe('save', function() {
        it('calls validation and api with goals', function() {
            var deferred = $q.defer();
            $scope.campaignGoal = 'goal';
            $scope.errors = {};

            spyOn(api.campaignGoalValidation, 'post').and.callFake(function() {
                return deferred.promise;
            });
            spyOn($scope, 'validate').and.callFake(function() {
                return true;
            });
            spyOn($scope, '$close');

            $scope.save();

            expect($scope.validate).toHaveBeenCalled();
            expect(api.campaignGoalValidation.post).toHaveBeenCalledWith(
                1,
                'goal'
            );

            $timeout(function() {
                expect($scope.$close).toHaveBeenCalled();
            }, 1500);
        });

        it('calls validation, api and adds conversion pixel', function() {
            var deferred = $q.defer();
            $scope.campaignGoal = {
                name: 'conversion goal',
                conversionGoal: {
                    goalId: '___new___',
                    type: constants.conversionGoalType.PIXEL,
                },
            };
            $scope.errors = {};
            $scope.newPixel = {
                name: 'awesome pixel',
            };

            spyOn(api.conversionPixel, 'post').and.callFake(function() {
                return deferred.promise;
            });

            spyOn(api.campaignGoalValidation, 'post').and.callFake(function() {
                return deferred.promise;
            });
            spyOn($scope, 'validate').and.callFake(function() {
                return true;
            });
            spyOn($scope, '$close');

            $scope.save();

            expect($scope.validate).toHaveBeenCalled();
            expect(api.conversionPixel.post).toHaveBeenCalledWith(1, {
                name: 'awesome pixel',
            });

            $timeout(function() {
                expect($scope.$close).toHaveBeenCalled();
            }, 1500);
        });

        it("doesn't call api if validation fails", function() {
            var deferred = $q.defer();

            $scope.campaignGoal = 'goal';
            $scope.errors = {};
            spyOn(api.campaignGoalValidation, 'post').and.callFake(function() {
                return deferred.promise;
            });
            spyOn($scope, 'validate').and.callFake(function() {
                return false;
            });
            $scope.save();
            expect($scope.validate).toHaveBeenCalled();
            expect(api.campaignGoalValidation.post).not.toHaveBeenCalled();
        });
    });

    describe('validate', function() {
        it('catches duplicate conversion goal ids', function() {
            var newGoal = {},
                errors = {};
            $scope.campaignGoals = [
                {
                    primary: false,
                    campaignId: 1,
                    id: 1,
                    type: 4,
                    conversionGoal: {
                        goalId: '123',
                        type: 2,
                        name: '123',
                    },
                },
                {
                    primary: true,
                    campaignId: 1,
                    type: 4,
                    conversionGoal: {
                        goalId: '123',
                        type: 3,
                        name: '124',
                    },
                },
            ];

            newGoal = {
                type: 4,
                campaignId: 1,
                conversionGoal: {
                    goalId: '123',
                    type: 3,
                    name: '125',
                },
            };

            expect($scope.validate(newGoal, errors)).toBe(false);

            newGoal = {
                type: 4,
                campaignId: 1,
                conversionGoal: {
                    goalId: '124',
                    type: 3,
                    name: '125',
                },
            };

            expect($scope.validate(newGoal, errors)).toBe(true);
        });
        it('recognizes modified existing goals', function() {
            var newGoal = {},
                errors = {};
            $scope.campaignGoals = [
                {
                    primary: false,
                    campaignId: 1,
                    id: 1,
                    type: 4,
                    conversionGoal: {
                        goalId: '123',
                        type: 2,
                        name: '123',
                    },
                },
                {
                    primary: true,
                    campaignId: 1,
                    type: 4,
                    conversionGoal: {
                        goalId: '123',
                        type: 3,
                        name: '124',
                    },
                },
            ];

            newGoal = {
                type: 4,
                campaignId: 1,
                id: 1,
                conversionGoal: {
                    goalId: '123',
                    type: 2,
                    name: '128',
                },
            };

            expect($scope.validate(newGoal, errors)).toBe(true);
        });

        it('allows only different conversion windows for same pixie', function() {
            var newGoal = {},
                errors = {};
            $scope.campaignGoals = [
                {
                    primary: false,
                    campaignId: 1,
                    id: 1,
                    type: 4,
                    conversionGoal: {
                        goalId: '123',
                        type: 1,
                        name: '123',
                        conversionWindow: 1,
                    },
                },
                {
                    primary: true,
                    campaignId: 1,
                    type: 4,
                    conversionGoal: {
                        goalId: '123',
                        type: 1,
                        name: '124',
                        conversionWindow: 2,
                    },
                },
            ];

            newGoal = {
                type: 4,
                campaignId: 1,
                conversionGoal: {
                    goalId: '123',
                    type: 1,
                    name: '125',
                    conversionWindow: 2,
                },
            };

            expect($scope.validate(newGoal, errors)).toBe(false);

            newGoal = {
                type: 4,
                campaignId: 1,
                conversionGoal: {
                    goalId: '124',
                    type: 3,
                    name: '125',
                    conversionWindow: 3,
                },
            };

            expect($scope.validate(newGoal, errors)).toBe(true);
        });
    });
});
