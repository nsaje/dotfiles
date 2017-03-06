/* globals it, describe, inject, module, expect, spyOn, beforeEach */
'use strict';

describe('AddConversionPixelModalCtrl', function () {
    var $scope, api, $q, $timeout, openedDeferred, audiencePixel;

    beforeEach(module('one'));
    beforeEach(module('one.mocks.zemInitializationService'));
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

        audiencePixel = {
            id: 2,
            name: 'Test Name Audience',
            audienceEnabled: true
        };

        $controller(
            'AddConversionPixelModalCtrl',
            {$scope: $scope, api: api, audiencePixel: audiencePixel}
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
            expect($scope.hasErrors).toEqual(false);
            expect($scope.validationErrors).toEqual({});

            var errors = {'name': ['error']};

            deferred.reject({errors: errors});
            $scope.$digest();

            expect($scope.inProgress).toBe(false);
            expect($scope.$close).not.toHaveBeenCalled();
            expect($scope.hasErrors).toEqual(false);
            expect($scope.validationErrors).toEqual(errors);
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
