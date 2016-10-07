/* globals it, describe, inject, module, expect, spyOn, beforeEach */
'use strict';

describe('AddConversionPixelModalCtrl', function () {
    var $scope, api, $q, $timeout, openedDeferred, outbrainPixel;

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
                post: mockApiFunc
            }
        };

        outbrainPixel = {
            id: 2,
            name: 'Test Name Outbrain',
            outbrainSync: true
        };

        $controller(
            'AddConversionPixelModalCtrl',
            {$scope: $scope, api: api, outbrainPixel: outbrainPixel}
        );
    }));

    describe('submit', function () {
        it('updates error message on failure', function () {
            var deferred = $q.defer();

            spyOn(api.conversionPixel, 'post').and.callFake(function () {
                return deferred.promise;
            });

            spyOn($scope, '$close');

            $scope.submit('slug');
            $scope.$digest();

            expect(api.conversionPixel.post).toHaveBeenCalled();
            expect($scope.inProgress).toBe(true);
            expect($scope.$close).not.toHaveBeenCalled();
            expect($scope.error).toEqual(false);
            expect($scope.errorMessage).toEqual('');

            deferred.reject({message: 'error message'});
            $scope.$digest();

            expect($scope.inProgress).toBe(false);
            expect($scope.$close).not.toHaveBeenCalled();
            expect($scope.error).toEqual(true);
            expect($scope.errorMessage).toEqual('error message');
        });

        it('closes the modal window on success', function () {
            var deferred = $q.defer();

            spyOn(api.conversionPixel, 'post').and.callFake(function () {
                return deferred.promise;
            });

            spyOn($scope, '$close');

            $scope.submit('slug');
            $scope.$digest();

            expect(api.conversionPixel.post).toHaveBeenCalled();
            expect($scope.inProgress).toBe(true);
            expect($scope.$close).not.toHaveBeenCalled();

            deferred.resolve({id: 1, slug: 'slug', archived: false, lastVerifiedDt: null, status: 1});
            $scope.$digest();

            expect($scope.inProgress).toBe(false);
            expect($scope.$close).toHaveBeenCalledWith({id: 1, slug: 'slug', archived: false, lastVerifiedDt: null, status: 1});
        });
    });
});
