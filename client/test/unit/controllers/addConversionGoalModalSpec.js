'use strict';

describe('AddConversionGoalModalCtrl', function () {
    var $scope, $modalInstance, api, $q, $timeout, openedDeferred;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(inject(function ($controller, $rootScope, _$q_, _$timeout_) {
        $q = _$q_;
        $timeout = _$timeout_;
        $scope = $rootScope.$new();
        $scope.campaign = {
            id: 1
        };

        openedDeferred = $q.defer();
        $modalInstance = {
            close: function () {},
            opened: openedDeferred.promise
        };

        var mockApiFunc = function () {
            return {
                then: function () {
                    return {
                        finally: function () {}
                    };
                }
            };
        };

        api = {
            conversionGoal: {
                post: mockApiFunc
            }
        };

        $controller(
            'AddConversionGoalModalCtrl',
            {$scope: $scope, $modalInstance: $modalInstance, api: api}
        );
    }));

    describe('addConversionGoal', function () {
        it('updates errors object on known errors', function () {
            var deferred = $q.defer();

            spyOn(api.conversionGoal, 'post').and.callFake(function () {
                return deferred.promise;
            });

            spyOn($modalInstance, 'close');

            $scope.addConversionGoal();
            $scope.$digest();

            expect(api.conversionGoal.post).toHaveBeenCalledWith(1, {});
            expect($scope.addConversionGoalInProgress).toBe(true);
            expect($modalInstance.close).not.toHaveBeenCalled();
            expect($scope.error).toEqual(false);
            expect($scope.errors).toEqual({});

            deferred.reject({'err': ['Error']});
            $scope.$digest();

            expect($scope.addConversionGoalInProgress).toBe(false);
            expect($modalInstance.close).not.toHaveBeenCalled();
            expect($scope.error).toEqual(false);
            expect($scope.errors).toEqual({'err': ['Error']});
        });

        it('updates error flag on unknown error', function () {
            var deferred = $q.defer();

            spyOn(api.conversionGoal, 'post').and.callFake(function () {
                return deferred.promise;
            });

            spyOn($modalInstance, 'close');

            $scope.addConversionGoal();
            $scope.$digest();

            expect(api.conversionGoal.post).toHaveBeenCalledWith(1, {});
            expect($scope.addConversionGoalInProgress).toBe(true);
            expect($modalInstance.close).not.toHaveBeenCalled();
            expect($scope.error).toEqual(false);
            expect($scope.errors).toEqual({});

            deferred.reject(null);
            $scope.$digest();

            expect($scope.addConversionGoalInProgress).toBe(false);
            expect($modalInstance.close).not.toHaveBeenCalled();
            expect($scope.error).toEqual(true);
            expect($scope.errors).toEqual({});
        });

        it('closes the modal window on success', function () {
            var deferred = $q.defer();

            spyOn(api.conversionGoal, 'post').and.callFake(function () {
                return deferred.promise;
            });

            spyOn($modalInstance, 'close');

            $scope.addConversionGoal();
            $scope.$digest();

            expect(api.conversionGoal.post).toHaveBeenCalledWith(1, {});
            expect($scope.addConversionGoalInProgress).toBe(true);
            expect($modalInstance.close).not.toHaveBeenCalled();

            deferred.resolve();
            $scope.$digest();

            expect($scope.addConversionGoalInProgress).toBe(false);
            expect($modalInstance.close).toHaveBeenCalled();
        });
    });
});
