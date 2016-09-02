/* globals describe, beforeEach, module, inject, it, expect, constants, angular, spyOn, jasmine */
'use strict';

describe('ZemUploadStep0Ctrl', function () {
    var scope, $modalInstance, $q, ctrl;

    beforeEach(module('one'));
    beforeEach(inject(function ($controller, $rootScope, _$q_) {
        $q = _$q_;
        scope = $rootScope.$new();
        var mockEndpoint = {
            createBatch: function () {},
        };

        ctrl = $controller(
            'ZemUploadStep0Ctrl',
            {$scope: scope},
            {
                endpoint: mockEndpoint,
                defaultBatchName: 'default batch name',
                singleUploadCallback: function () {},
                csvUploadCallback: function () {},
                close: function () {},
            }
        );
    }));

    it('switches to single content ad upload', function () {
        var deferred = $q.defer();
        spyOn(ctrl.endpoint, 'createBatch').and.callFake(function () {
            return deferred.promise;
        });

        spyOn(ctrl, 'singleUploadCallback').and.stub();
        ctrl.switchToSingleContentAdUpload();

        deferred.resolve({
            batchId: 1234,
            batchName: 'batch name',
        });
        scope.$digest();

        expect(ctrl.singleUploadCallback).toHaveBeenCalledWith({
            batchId: 1234,
            batchName: 'batch name',
            candidates: [],
        });
    });

    it('switches to csv upload', function () {
        spyOn(ctrl, 'csvUploadCallback').and.stub();
        ctrl.switchToCsvUpload();
        expect(ctrl.csvUploadCallback).toHaveBeenCalled();
    });
});
