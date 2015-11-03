'use strict';

describe('CampaignAgencyCtrl', function () {
    var $modalStack, $scope, $state, $q, api;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(function () {
        inject(function ($rootScope, $controller, _$state_, _$q_, _$modalStack_) {
            $q = _$q_;
            $scope = $rootScope.$new();

            $scope.isPermissionInternal = function() {return true;};
            $scope.hasPermission = function() {return true;};
            $scope.campaign = {id: 1};
            $scope.getConversionPixelTag = function () {return '';};

            var mockApiFunc = function() {
                return {
                    then: function() {
                        return {
                            finally: function() {}
                        };
                    }
                };
            };

            api = {
                conversionGoal: {
                    list: mockApiFunc,
                    post: mockApiFunc,
                    delete: mockApiFunc
                },
                campaignAgency: {
                    get: mockApiFunc
                }
            };

            $state = _$state_;
            $state.params = {id: 1};

            $modalStack = _$modalStack_;

            $controller('CampaignAgencyCtrl', {$scope: $scope, api: api});
        });
    });

    describe('addConversionGoal', function(done) {
        it('opens a modal window', function () {
            $scope.addConversionGoal().result
                .catch(function(error) {
                    expect(error).toBeUndefined();
                })
                .finally(done);
        });
    });

    describe('listConversionGoals', function() {
        beforeEach(function() {
            $scope.conversionPixels = [];
        });

        it('sets error to true on failure', function () {
            var deferred = $q.defer();

            spyOn(api.conversionGoal, 'list').and.callFake(function () {
                return deferred.promise;
            });

            $scope.getConversionGoals();
            $scope.$digest();

            expect($scope.goalsRequestInProgress).toBe(true);

            deferred.reject();
            $scope.$digest();

            expect($scope.goalsRequestInProgress).toBe(false);
            expect(api.conversionGoal.list).toHaveBeenCalled();
            expect($scope.conversionGoals).toEqual([]);
            expect($scope.goalsError).toEqual(true);
        });

        it('populates conversion pixels array on success', function () {
            var deferred = $q.defer();

            spyOn(api.conversionGoal, 'list').and.callFake(function () {
                return deferred.promise;
            });

            $scope.getConversionGoals();
            $scope.$digest();

            expect($scope.goalsRequestInProgress).toBe(true);

            deferred.resolve(
                {
                    rows: [{id: 1, type: 2, name: 'conversion goal', conversionWindow: null, goalId: '1'}],
                    availablePixels: [{id: 1, slug: 'slug'}]
                }
            );
            $scope.$digest();

            expect($scope.goalsRequestInProgress).toBe(false);
            expect(api.conversionGoal.list).toHaveBeenCalled();
            expect($scope.conversionGoals).toEqual([{id: 1, rows :[{title: 'Name', value: 'conversion goal'}, {title: 'Type', value: 'Google Analytics'}, {title: 'Goal name', value: '1'}]}]);
            expect($scope.availablePixels).toEqual([{id: 1, slug: 'slug'}]);
            expect($scope.goalsError).toEqual(false);
        });
    });

    describe('removeConversionGoal', function() {
        it('sets error flag on failure', function () {
            var deferred = $q.defer();

            spyOn(api.conversionGoal, 'delete').and.callFake(function() {
                return deferred.promise;
            });
            spyOn($scope, 'getSettings');

            $scope.conversionGoals = [{id: 1, rows :[{title: 'Name', value: 'conversion goal'}, {title: 'Type', value: 'Google Analytics'}, {title: 'Goal name', value: '1'}]}];
            $scope.removeConversionGoal(1, 1);
            $scope.$digest();

            expect($scope.goalsRequestInProgress).toBe(true);

            deferred.reject();
            $scope.$digest();

            expect(api.conversionGoal.delete).toHaveBeenCalled();
            expect($scope.getSettings).not.toHaveBeenCalled();
            expect($scope.goalsError).toBe(true);
            expect($scope.conversionGoals).toEqual([{id: 1, rows :[{title: 'Name', value: 'conversion goal'}, {title: 'Type', value: 'Google Analytics'}, {title: 'Goal name', value: '1'}]}]);
        });

        it('updates history on success', function() {
            var deferred = $q.defer();

            spyOn(api.conversionGoal, 'delete').and.callFake(function() {
                return deferred.promise;
            });
            spyOn($scope, 'getSettings');

            $scope.conversionGoals = [{id: 1, rows :[{title: 'Name', value: 'conversion goal'}, {title: 'Type', value: 'Google Analytics'}, {title: 'Goal name', value: '1'}]}];
            $scope.removeConversionGoal(1, 1);
            $scope.$digest();

            expect($scope.goalsRequestInProgress).toBe(true);

            deferred.resolve();
            $scope.$digest();

            expect(api.conversionGoal.delete).toHaveBeenCalled();
            expect($scope.getSettings).toHaveBeenCalled();
            expect($scope.goalsError).toBe(false);
            expect($scope.conversionGoals).toEqual([]);
        });
    });
});
