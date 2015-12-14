'use strict';

describe('zemConversionPixels', function () {
    var $scope, $q, element, isolate;

    var mockApiFunc = function() {
        return {
            then: function() {
                return {
                    finally: function() {}
                };
            }
        };
    };

    var api = {
        conversionPixel: {
            list: mockApiFunc,
            post: mockApiFunc,
            archive: mockApiFunc,
            restore: mockApiFunc
        }
    };

    angular.module('apiMock', []);
    angular.module('apiMock').service('api', function () {
        return api;
    });

    beforeEach(module('one'));
    beforeEach(module('apiMock'));

    beforeEach(inject(function ($compile, $rootScope, _$q_) {
        $q =  _$q_;
        var template = '<zem-conversion-pixels zem-account="account" zem-has-permission="hasPermission" zem-is-permission-internal="isPermissionInternal"></zem-conversion-pixels>';

        $scope = $rootScope.$new();
        $scope.isPermissionInternal = function() {return true;};
        $scope.hasPermission = function() {return true;};
        $scope.account = {id: 1};

        element = $compile(template)($scope);

        $scope.$digest();
        isolate = element.isolateScope();
    }));

    describe('addConversionPixel', function(done) {
        it('opens a modal window', function () {
            isolate.addConversionPixel().result
                .catch(function(error) {
                    expect(error).toBeUndefined();
                })
                .finally(done);
        });
    });

    describe('copyConversionPixelTag', function(done) {
        it('opens a modal window', function () {
            isolate.copyConversionPixelTag({id: 1, slug: 'slug', status: 1, lastVerifiedDt: null, archived: false, url: ''}).result
                .catch(function(error) {
                    expect(error).toBeUndefined();
                })
                .finally(done);
        });
    });

    describe('listConversionPixels', function() {
        beforeEach(function() {
            isolate.conversionPixels = [];
        });

        it('does nothing on failure', function () {
            var deferred = $q.defer();

            spyOn(api.conversionPixel, 'list').and.callFake(function () {
                return deferred.promise;
            });

            isolate.getConversionPixels();
            isolate.$digest();

            expect(isolate.listInProgress).toBe(true);

            deferred.reject();
            isolate.$digest();

            expect(isolate.listInProgress).toBe(false);
            expect(api.conversionPixel.list).toHaveBeenCalled();
            expect(isolate.conversionPixels).toEqual([]);
        });

        it('populates conversion pixels array on success', function () {
            var deferred = $q.defer();

            spyOn(api.conversionPixel, 'list').and.callFake(function () {
                return deferred.promise;
            });

            isolate.getConversionPixels();
            isolate.$digest();

            expect(isolate.listInProgress).toBe(true);

            deferred.resolve({rows: [{id: 1, slug: 'abc', archived: false, status: 1, lastVerifiedDt: null}], tagPrefix: 'test'});
            isolate.$digest();

            expect(isolate.listInProgress).toBe(false);
            expect(api.conversionPixel.list).toHaveBeenCalled();

            expect(angular.equals(isolate.conversionPixels, [{id: 1, slug: 'abc', archived: false, status: 1, lastVerifiedDt: null}])).toEqual(true);
            expect(isolate.tagPrefix).toEqual('test');
        });
    });

    describe('archiveConversionPixel', function() {
        beforeEach(function() {
            isolate.conversionPixels = [{id: 1, archived: false, status: 1, slug: 'slug', lastVerifiedDt: null}];
        });

        it('does nothing on failure', function() {
            var deferred = $q.defer();

            spyOn(api.conversionPixel, 'archive').and.callFake(function() {
                return deferred.promise;
            });

            isolate.conversionPixels = [{id: 1, slug: 'slug', url: '', archived: false, lastVerifiedDt: null}];

            isolate.archiveConversionPixel(isolate.conversionPixels[0]);
            isolate.$digest();

            expect(isolate.conversionPixels[0].requestInProgress).toBe(true);

            deferred.reject();
            isolate.$digest();

            expect(api.conversionPixel.archive).toHaveBeenCalled();
            expect(isolate.conversionPixels[0].archived).toBe(false);
            expect(isolate.conversionPixels[0].requestInProgress).toBe(false);
        });

        it('updates history on success', function() {
            var deferred = $q.defer();

            spyOn(api.conversionPixel, 'archive').and.callFake(function() {
                return deferred.promise;
            });

            isolate.conversionPixels = [{id: 1, slug: 'slug', url: '', archived: false, lastVerifiedDt: null}];

            isolate.archiveConversionPixel(isolate.conversionPixels[0]);
            isolate.$digest();

            expect(api.conversionPixel.archive).toHaveBeenCalled();
            expect(isolate.conversionPixels[0].archived).toBe(false);
            expect(isolate.conversionPixels[0].requestInProgress).toBe(true);

            deferred.resolve({id: 1, archived: true, status: 1, slug: 'slug', lastVerifiedDt: null});
            isolate.$digest();

            expect(isolate.conversionPixels[0].archived).toBe(true);
            expect(isolate.conversionPixels[0].requestInProgress).toBe(false);
        });
    });

    describe('restoreConversionPixel', function() {
        beforeEach(function() {
            isolate.conversionPixels = [{id: 1, archived: true, status: 1, slug: 'slug', lastVerifiedDt: null}];
        });

        it('does nothing on failure', function () {
            var deferred = $q.defer();

            spyOn(api.conversionPixel, 'restore').and.callFake(function() {
                return deferred.promise;
            });

            isolate.conversionPixels = [{id: 1, slug: 'slug', url: '', archived: true, lastVerifiedDt: null}];

            isolate.restoreConversionPixel(isolate.conversionPixels[0]);
            isolate.$digest();

            expect(isolate.conversionPixels[0].requestInProgress).toBe(true);

            deferred.reject();
            isolate.$digest();

            expect(api.conversionPixel.restore).toHaveBeenCalled();
            expect(isolate.conversionPixels[0].archived).toBe(true);
            expect(isolate.conversionPixels[0].requestInProgress).toBe(false);
        });

        it('updates history on success', function() {
            var deferred = $q.defer();

            spyOn(api.conversionPixel, 'restore').and.callFake(function() {
                return deferred.promise;
            });

            isolate.conversionPixels = [{id: 1, slug: 'slug', url: '', archived: true, lastVerifiedDt: null}];

            isolate.restoreConversionPixel(isolate.conversionPixels[0]);
            isolate.$digest();

            expect(api.conversionPixel.restore).toHaveBeenCalled();
            expect(isolate.conversionPixels[0].archived).toBe(true);
            expect(isolate.conversionPixels[0].requestInProgress).toBe(true);

            deferred.resolve({id: 1, archived: false, status: 1, slug: 'slug', lastVerifiedDt: null});
            isolate.$digest();

            expect(isolate.conversionPixels[0].archived).toBe(false);
            expect(isolate.conversionPixels[0].requestInProgress).toBe(false);
        });
    });
});
