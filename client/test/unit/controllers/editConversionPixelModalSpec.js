/* globals it, describe, inject, module, expect, spyOn, beforeEach */
'use strict';

describe('EditConversionPixelModalCtrl', function () {
    var $scope, api, $q, $timeout, openedDeferred, pixel, outbrainPixel;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(inject(function ($controller, $rootScope, _$q_, _$timeout_) {
        $q = _$q_;
        $timeout = _$timeout_;
        $scope = $rootScope.$new();
        $scope.$close = function () {};
        $scope.account = {
            id: 1
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
            conversionPixel: {
                edit: mockApiFunc
            }
        };

        pixel = {
            id: 1,
            name: 'Test Name',
            outbrainSync: false
        };

        outbrainPixel = {
            id: 2,
            name: 'Test Name Outbrain',
            outbrainSync: true
        };

        $controller(
            'EditConversionPixelModalCtrl',
            {$scope: $scope, api: api, pixel: pixel, outbrainPixel: outbrainPixel}
        );
    }));

    describe('editConversionPixel', function () {
        it('updates error message on failure', function () {
            var deferred = $q.defer();

            spyOn(api.conversionPixel, 'edit').and.callFake(function () {
                return deferred.promise;
            });

            spyOn($scope, '$close');

            $scope.submit();
            $scope.$digest();

            expect(api.conversionPixel.edit).toHaveBeenCalled();
            expect($scope.inProgress).toBe(true);
            expect($scope.$close).not.toHaveBeenCalled();
            expect($scope.error).toEqual(false);
            expect($scope.errorMessage).toEqual('');

            deferred.reject({errors: {name: ['error message', 'another message']}});
            $scope.$digest();

            expect($scope.inProgress).toBe(false);
            expect($scope.$close).not.toHaveBeenCalled();
            expect($scope.error).toEqual(true);
            expect($scope.errorMessage).toEqual('error message another message');
        });

        it('closes the modal window on success', function () {
            var deferred = $q.defer();

            spyOn(api.conversionPixel, 'edit').and.callFake(function () {
                return deferred.promise;
            });

            spyOn($scope, '$close');

            $scope.submit();
            $scope.$digest();

            expect(api.conversionPixel.edit).toHaveBeenCalled();
            expect($scope.inProgress).toBe(true);
            expect($scope.$close).not.toHaveBeenCalled();

            deferred.resolve({id: 1, name: 'name', archived: false, outbrain_sync: true});
            $scope.$digest();

            expect($scope.inProgress).toBe(false);
            expect($scope.$close).toHaveBeenCalledWith({id: 1, name: 'name', archived: false, outbrain_sync: true});
        });
    });
});
