'use strict';

describe('AddConversionPixelModalCtrl', function() {
    var $scope, $modalInstance, api, $state, $q, $timeout, openedDeferred;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(inject(function($controller, $rootScope, _$q_, _$timeout_, _$state_) {
        $q = _$q_;
        $timeout = _$timeout_;
        $scope = $rootScope.$new();
        $scope.account = {
            id: 1
        };

        openedDeferred = $q.defer();
        $modalInstance = {
            close: function(){},
            opened: openedDeferred.promise
        };

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
            conversionPixel: {
                post: mockApiFunc
            }
        };

        $state = _$state_;
        $state.params = {
            id: 1
        };

        $controller(
            'AddConversionPixelModalCtrl',
            {$scope: $scope, $modalInstance: $modalInstance, $state: $state, api: api}
        );
    }));

    describe('addConversionPixel', function() {
        it('updates error message on failure', function() {
            var deferred = $q.defer();

            spyOn(api.conversionPixel, 'post').and.callFake(function() {
                return deferred.promise;
            });

            spyOn($modalInstance, 'close');

            $scope.addConversionPixel('slug');
            $scope.$digest();

            expect(api.conversionPixel.post).toHaveBeenCalled();
            expect($scope.addConversionPixelInProgress).toBe(true);
            expect($modalInstance.close).not.toHaveBeenCalled();

            deferred.reject({message: 'error message'});
            $scope.$digest();

            expect($scope.addConversionPixelInProgress).toBe(false);
            expect($modalInstance.close).not.toHaveBeenCalled();
            expect($scope.error).toEqual('error message');
        });

        it('closes the modal window on success', function() {
            var deferred = $q.defer();

            spyOn(api.conversionPixel, 'post').and.callFake(function() {
                return deferred.promise;
            });

            spyOn($modalInstance, 'close');

            $scope.addConversionPixel('slug');
            $scope.$digest();

            expect(api.conversionPixel.post).toHaveBeenCalled();
            expect($scope.addConversionPixelInProgress).toBe(true);
            expect($modalInstance.close).not.toHaveBeenCalled();

            deferred.resolve({id: 1, slug: 'slug', archived: false, lastVerifiedDt: null, status: 1});
            $scope.$digest();

            expect($scope.addConversionPixelInProgress).toBe(false);
            expect($modalInstance.close).toHaveBeenCalledWith({id: 1, slug: 'slug', archived: false, lastVerifiedDt: null, status: 1});
        });
    });
});
