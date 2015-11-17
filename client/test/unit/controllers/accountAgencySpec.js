'use strict';

describe('AccountAgencyCtrl', function () {
    var $modalStack, $scope, $state, $q, api;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(function () {
        inject(function ($rootScope, $controller, _$state_, _$q_, _$modalStack_) {
            $q = _$q_;
            $scope = $rootScope.$new();

            $scope.isPermissionInternal = function() {return true;};
            $scope.hasPermission = function() {return true;};
            $scope.account = {id: 1};
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
                conversionPixel: {
                    list: mockApiFunc,
                    post: mockApiFunc,
                    archive: mockApiFunc,
                    restore: mockApiFunc
                },
                accountAgency: {
                    get: mockApiFunc
                },
                accountUsers: {
                    list: mockApiFunc
                }
            };

            $state = _$state_;
            $state.params = {id: 1};

            $modalStack = _$modalStack_;

            $controller('AccountAgencyCtrl', {$scope: $scope, api: api});
        });
    });

    describe('addConversionPixel', function(done) {
        it('opens a modal window', function () {
            $scope.addConversionPixel().result
                .catch(function(error) {
                    expect(error).toBeUndefined();
                })
                .finally(done);
        });
    });

    describe('copyConversionPixelTag', function(done) {
        it('opens a modal window', function () {
            $scope.copyConversionPixelTag({id: 1, slug: 'slug', status: 1, lastVerifiedDt: null, archived: false, url: ''}).result
                .catch(function(error) {
                    expect(error).toBeUndefined();
                })
                .finally(done);
        });
    });

    describe('listConversionPixels', function() {
        beforeEach(function() {
            $scope.conversionPixels = [];
        });

        it('does nothing on failure', function () {
            var deferred = $q.defer();

            spyOn(api.conversionPixel, 'list').and.callFake(function () {
                return deferred.promise;
            });

            $scope.getConversionPixels();
            $scope.$digest();

            expect($scope.listPixelsInProgress).toBe(true);

            deferred.reject();
            $scope.$digest();

            expect($scope.listPixelsInProgress).toBe(false);
            expect(api.conversionPixel.list).toHaveBeenCalled();
            expect($scope.conversionPixels).toEqual([]);
        });

        it('populates conversion pixels array on success', function () {
            var deferred = $q.defer();

            spyOn(api.conversionPixel, 'list').and.callFake(function () {
                return deferred.promise;
            });

            $scope.getConversionPixels();
            $scope.$digest();

            expect($scope.listPixelsInProgress).toBe(true);

            deferred.resolve({rows: [{id: 1, slug: 'abc', archived: false, status: 1, lastVerifiedDt: null}], conversionPixelTagPrefix: 'test'});
            $scope.$digest();

            expect($scope.listPixelsInProgress).toBe(false);
            expect(api.conversionPixel.list).toHaveBeenCalled();
            expect($scope.conversionPixels).toEqual([{id: 1, slug: 'abc', archived: false, status: 1, lastVerifiedDt: null}]);
            expect($scope.conversionPixelTagPrefix).toEqual('test');
        });
    });

    describe('archiveConversionPixel', function() {
        beforeEach(function() {
            $scope.conversionPixels = [{id: 1, archived: false, status: 1, slug: 'slug', lastVerifiedDt: null}];
        });

        it('does nothing on failure', function() {
            var deferred = $q.defer();

            spyOn(api.conversionPixel, 'archive').and.callFake(function() {
                return deferred.promise;
            });
            spyOn($scope, 'getSettings');

            $scope.conversionPixels = [{id: 1, slug: 'slug', url: '', archived: false, lastVerifiedDt: null}];

            $scope.archiveConversionPixel($scope.conversionPixels[0]);
            $scope.$digest();

            expect($scope.conversionPixels[0].requestInProgress).toBe(true);

            deferred.reject();
            $scope.$digest();

            expect(api.conversionPixel.archive).toHaveBeenCalled();
            expect($scope.getSettings).not.toHaveBeenCalled();
            expect($scope.conversionPixels[0].archived).toBe(false);
            expect($scope.conversionPixels[0].requestInProgress).toBe(false);
        });

        it('updates history on success', function() {
            var deferred = $q.defer();

            spyOn(api.conversionPixel, 'archive').and.callFake(function() {
                return deferred.promise;
            });
            spyOn($scope, 'getSettings');

            $scope.conversionPixels = [{id: 1, slug: 'slug', url: '', archived: false, lastVerifiedDt: null}];

            $scope.archiveConversionPixel($scope.conversionPixels[0]);
            $scope.$digest();

            expect(api.conversionPixel.archive).toHaveBeenCalled();
            expect($scope.getSettings).not.toHaveBeenCalled();
            expect($scope.conversionPixels[0].archived).toBe(false);
            expect($scope.conversionPixels[0].requestInProgress).toBe(true);

            deferred.resolve({id: 1, archived: true, status: 1, slug: 'slug', lastVerifiedDt: null});
            $scope.$digest();

            expect($scope.getSettings).toHaveBeenCalled();
            expect($scope.conversionPixels[0].archived).toBe(true);
            expect($scope.conversionPixels[0].requestInProgress).toBe(false);
        });
    });

    describe('restoreConversionPixel', function() {
        beforeEach(function() {
            $scope.conversionPixels = [{id: 1, archived: true, status: 1, slug: 'slug', lastVerifiedDt: null}];
        });

        it('does nothing on failure', function () {
            var deferred = $q.defer();

            spyOn(api.conversionPixel, 'restore').and.callFake(function() {
                return deferred.promise;
            });
            spyOn($scope, 'getSettings');

            $scope.conversionPixels = [{id: 1, slug: 'slug', url: '', archived: true, lastVerifiedDt: null}];

            $scope.restoreConversionPixel($scope.conversionPixels[0]);
            $scope.$digest();

            expect($scope.conversionPixels[0].requestInProgress).toBe(true);

            deferred.reject();
            $scope.$digest();

            expect(api.conversionPixel.restore).toHaveBeenCalled();
            expect($scope.getSettings).not.toHaveBeenCalled();
            expect($scope.conversionPixels[0].archived).toBe(true);
            expect($scope.conversionPixels[0].requestInProgress).toBe(false);
        });

        it('updates history on success', function() {
            var deferred = $q.defer();

            spyOn(api.conversionPixel, 'restore').and.callFake(function() {
                return deferred.promise;
            });
            spyOn($scope, 'getSettings');

            $scope.conversionPixels = [{id: 1, slug: 'slug', url: '', archived: true, lastVerifiedDt: null}];

            $scope.restoreConversionPixel($scope.conversionPixels[0]);
            $scope.$digest();

            expect(api.conversionPixel.restore).toHaveBeenCalled();
            expect($scope.getSettings).not.toHaveBeenCalled();
            expect($scope.conversionPixels[0].archived).toBe(true);
            expect($scope.conversionPixels[0].requestInProgress).toBe(true);

            deferred.resolve({id: 1, archived: false, status: 1, slug: 'slug', lastVerifiedDt: null});
            $scope.$digest();

            expect($scope.getSettings).toHaveBeenCalled();
            expect($scope.conversionPixels[0].archived).toBe(false);
            expect($scope.conversionPixels[0].requestInProgress).toBe(false);
        });
    });
});
