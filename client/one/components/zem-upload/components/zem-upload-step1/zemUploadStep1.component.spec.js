/* globals describe, beforeEach, module, inject, it, expect, constants, angular, spyOn, jasmine */
'use strict';

describe('ZemUploadStep1Ctrl', function () {
    var scope, $modalInstance, api, $q, ctrl;

    beforeEach(module('one'));
    beforeEach(inject(function ($controller, $rootScope, _$q_) {
        $q = _$q_;
        scope = $rootScope.$new();
        var mockApi = {
            upload: function () {},
            checkStatus: function () {},
            updateCandidate: function () {},
            removeCandidate: function () {},
            save: function () {},
            cancel: function () {},
        };

        var mockedDate = new Date(Date.UTC(2016, 6, 1, 15, 5));
        jasmine.clock().mockDate(mockedDate);

        ctrl = $controller(
            'ZemUploadStep1Ctrl',
            {$scope: scope},
            {
                api: mockApi,
                callback: function () {},
            }
        );
    }));

    it('switches to picker on success', function () {
        var deferred = $q.defer();
        spyOn(ctrl.api, 'upload').and.callFake(function () {
            return deferred.promise;
        });

        ctrl.formData = {
            file: 'testfile',
            batchName: 'testname',
        };
        ctrl.formData.file = 'testfile';
        spyOn(ctrl, 'callback').and.stub();

        ctrl.upload();
        expect(ctrl.api.upload).toHaveBeenCalledWith(
            {file: ctrl.formData.file, batchName: ctrl.formData.batchName}
        );
        expect(ctrl.requestInProgress).toBe(true);

        var candidates = [{
            id: 1,
            url: 'http://example.com/url1',
            title: 'Title 1',
            imageUrl: 'http://exmaple.com/img1.jpg',
            imageCrop: 'center',
            description: '',
            displayUrl: 'example.com',
            brandName: '',
            callToAction: 'Read more',
            label: 'title1',
            imageStatus: constants.asyncUploadJobStatus.WAITING_RESPONSE,
            urlStatus: constants.asyncUploadJobStatus.WAITING_RESPONSE,
        }];
        var batchId = 1234;
        var batchName = 'mock batch';
        deferred.resolve({
            candidates: candidates,
            batchName: batchName,
            batchId: batchId,
        });
        scope.$digest();

        expect(ctrl.callback).toHaveBeenCalledWith({
            batchId: batchId,
            batchName: batchName,
            candidates: candidates,
        });
        expect(ctrl.requestInProgress).toBe(false);
        expect(ctrl.requestFailed).toBe(false);
    });

    it('sets a flag on upload failure', function () {
        var deferred = $q.defer();
        spyOn(ctrl.api, 'upload').and.callFake(function () {
            return deferred.promise;
        });

        ctrl.formData = {
            file: 'testfile',
            batchName: 'testname',
        };
        ctrl.formData.file = 'testfile';
        spyOn(ctrl, 'callback').and.stub();

        ctrl.upload();
        expect(ctrl.api.upload).toHaveBeenCalledWith(
            {file: ctrl.formData.file, batchName: ctrl.formData.batchName}
        );
        expect(ctrl.requestInProgress).toBe(true);
        expect(ctrl.requestFailed).toBe(false);

        deferred.reject({});
        scope.$digest();

        expect(ctrl.requestInProgress).toBe(false);
        expect(ctrl.requestFailed).toBe(true);
        expect(ctrl.callback).not.toHaveBeenCalled();
    });

    it('uses current datetime as default batch name', function () {
        expect(ctrl.formData.batchName).toEqual('7/1/2016 3:05 PM');
    });

    it('displays errors on failure', function () {
        var deferred = $q.defer();
        spyOn(ctrl.api, 'upload').and.callFake(function () {
            return deferred.promise;
        });

        ctrl.formData = {
            file: 'testfile',
            batchName: 'testname',
        };
        spyOn(ctrl, 'callback').and.stub();

        ctrl.upload();
        expect(ctrl.api.upload).toHaveBeenCalledWith(
            {file: ctrl.formData.file, batchName: ctrl.formData.batchName}
        );

        var errors = {
            batchName: ['Missing batch name'],
            file: ['Missing file'],
        };
        deferred.reject({
            errors: errors,
        });
        scope.$digest();

        expect(ctrl.formErrors).toEqual(errors);
        expect(ctrl.callback).not.toHaveBeenCalled();
    });
});
