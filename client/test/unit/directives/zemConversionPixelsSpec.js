/* globals it, angular, describe, inject, module, expect, spyOn, beforeEach */
'use strict';

describe('zemConversionPixelsLegacy', function () {
    var $scope, $q, element, isolate, $uibModal;

    var mockApiFunc = function () {
        return {
            then: function () {
                return {
                    finally: function () {}
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

    var fakeModal = {
        result: {
            then: function (confirmCallback, cancelCallback) {
                this.confirmCallBack = confirmCallback;
                this.cancelCallback = cancelCallback;
            }
        },
        close: function (item) {
            this.result.confirmCallBack(item);
        },
        dismiss: function (type) {
            this.result.cancelCallback(type);
        }
    };

    angular.module('conversionPixelsApiMock', []);
    angular.module('conversionPixelsApiMock').service('api', function () {
        return api;
    });

    beforeEach(module('one'));
    beforeEach(module('conversionPixelsApiMock'));

    beforeEach(inject(function ($compile, $rootScope, _$q_, _$uibModal_) {
        $q =  _$q_;
        $uibModal = _$uibModal_;

        var template = '<zem-conversion-pixels-legacy zem-account="account" zem-has-permission="hasPermission" zem-is-permission-internal="isPermissionInternal"></zem-conversion-pixels-legacy>';

        $scope = $rootScope.$new();
        $scope.isPermissionInternal = function () { return true; };
        $scope.hasPermission = function () { return true; };
        $scope.account = {id: 1};

        element = $compile(template)($scope);

        $scope.$digest();
        isolate = element.isolateScope();
    }));

    describe('addConversionPixel', function () {
        it('opens a modal window', function () {
            isolate.addConversionPixel().result
                .catch(function (error) {
                    expect(error).toBeUndefined();
                });
        });
    });

    describe('editConversionPixel', function () {
        it('opens a modal window', function () {
            isolate.editConversionPixel({id: 1, name: 'test', audienceEnabled: true}).result
                .catch(function (error) {
                    expect(error).toBeUndefined();
                });
        });

        it('updates conversion pixels', function () {
            isolate.conversionPixels = [
                {id: 3, name: 'Old Name', archived: true, redirectUrl: 'http://test.com', notes: ''}
            ];

            spyOn($uibModal, 'open').and.returnValue(fakeModal);

            var modalInstance = isolate.editConversionPixel(isolate.conversionPixels[0]);
            modalInstance.close({id: 3, name: 'New Name', audienceEnabled: true, redirectUrl: 'http://newurl.com', notes: 'New Notes'});

            expect(isolate.conversionPixels).toEqual([
                {id: 3, name: 'New Name', archived: true, audienceEnabled: true, redirectUrl: 'http://newurl.com', notes: 'New Notes'}
            ]);
        });
    });

    describe('copyConversionPixelTag', function () {
        it('opens a modal window', function () {
            isolate.copyConversionPixelTag({id: 1, slug: 'slug', status: 1, lastVerifiedDt: null, archived: false, url: ''}).result
                .catch(function (error) {
                    expect(error).toBeUndefined();
                });
        });
    });

    describe('listConversionPixels', function () {
        beforeEach(function () {
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

    describe('archiveConversionPixel', function () {
        beforeEach(function () {
            isolate.conversionPixels = [{id: 1, archived: false, status: 1, slug: 'slug', lastVerifiedDt: null}];
        });

        it('does nothing on failure', function () {
            var deferred = $q.defer();

            spyOn(api.conversionPixel, 'archive').and.callFake(function () {
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

        it('updates history on success', function () {
            var deferred = $q.defer();

            spyOn(api.conversionPixel, 'archive').and.callFake(function () {
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

    describe('restoreConversionPixel', function () {
        beforeEach(function () {
            isolate.conversionPixels = [{id: 1, archived: true, status: 1, slug: 'slug', lastVerifiedDt: null}];
        });

        it('does nothing on failure', function () {
            var deferred = $q.defer();

            spyOn(api.conversionPixel, 'restore').and.callFake(function () {
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

        it('updates history on success', function () {
            var deferred = $q.defer();

            spyOn(api.conversionPixel, 'restore').and.callFake(function () {
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
