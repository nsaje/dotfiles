/* globals it, describe, inject, module, expect, spyOn, beforeEach */
'use strict';

describe('EditConversionPixelModalCtrl', function () {
    var $scope, api, $q, $timeout, openedDeferred, pixel, audiencePixel;

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
                put: mockApiFunc
            }
        };

        pixel = {
            id: 1,
            name: 'Test Name',
            audienceEnabled: false
        };

        audiencePixel = {
            id: 2,
            name: 'Test Name Audience',
            audienceEnabled: true
        };

        $controller(
            'EditConversionPixelModalCtrl',
            {$scope: $scope, api: api, pixel: pixel, audiencePixel: audiencePixel}
        );
    }));

    describe('editConversionPixel', function () {
        it('updates error message on failure', function () {
            var deferred = $q.defer();

            spyOn(api.conversionPixel, 'put').and.callFake(function () {
                return deferred.promise;
            });

            spyOn($scope, '$close');

            $scope.submit();
            $scope.$digest();

            expect(api.conversionPixel.put).toHaveBeenCalled();
            expect($scope.inProgress).toBe(true);
            expect($scope.$close).not.toHaveBeenCalled();
            expect($scope.hasErrors).toEqual(false);
            expect($scope.validationErrors).toEqual({});

            var errors = {name: ['error message', 'another message']};

            deferred.reject({errors: errors});
            $scope.$digest();

            expect($scope.inProgress).toBe(false);
            expect($scope.$close).not.toHaveBeenCalled();
            expect($scope.hasErrors).toEqual(false);
            expect($scope.validationErrors).toEqual(errors);
        });

        it('closes the modal window on success', function () {
            var deferred = $q.defer();

            spyOn(api.conversionPixel, 'put').and.callFake(function () {
                return deferred.promise;
            });

            spyOn($scope, '$close');

            $scope.submit();
            $scope.$digest();

            expect(api.conversionPixel.put).toHaveBeenCalled();
            expect($scope.inProgress).toBe(true);
            expect($scope.$close).not.toHaveBeenCalled();

            deferred.resolve({id: 1, name: 'name', archived: false, audience_enabled: true});
            $scope.$digest();

            expect($scope.inProgress).toBe(false);
            expect($scope.$close).toHaveBeenCalledWith({id: 1, name: 'name', archived: false, audience_enabled: true});
        });
    });
});
