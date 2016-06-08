/* globals describe, beforeEach, module, inject, constants, it, spyOn, expect */
'use strict';

describe('UploadAdsPlusModalCtrl', function () {
    var $scope, $modalInstance, api, $state, $q, $interval, openedDeferred;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(inject(function ($controller, $rootScope, _$q_, _$interval_, _$state_) {
        $q = _$q_;
        $interval = _$interval_;
        $scope = $rootScope.$new();
        $scope.$dismiss = function () {};

        openedDeferred = $q.defer();
        $modalInstance = {
            close: function () {},
            opened: openedDeferred.promise,
        };
        api = {
            uploadPlus: {
                uploadCsv: function () {},
                checkStatus: function () {},
                save: function () {},
                cancel: function () {},
                getDefaults: function () {
                    return {
                        then: function () {},
                    };
                },
            },
        };

        $state = _$state_;
        $state.params = {id: 123};

        $controller(
            'UploadAdsPlusModalCtrl',
            {$scope: $scope, $modalInstance: $modalInstance, api: api, $state: $state, errors: {}}
        );
    }));

    describe('upload', function () {
        it('calls api and polls for updates on success', function () {
            var deferred = $q.defer();
            var batchId = 123;
            var candidates = [1, 2, 3, 4];

            $scope.formData = {
                file: 'testfile',
                batchName: 'testname',
            };

            spyOn(api.uploadPlus, 'uploadCsv').and.callFake(function () {
                return deferred.promise;
            });
            spyOn($scope, 'pollBatchStatus');

            $scope.upload();

            expect(api.uploadPlus.uploadCsv).toHaveBeenCalledWith(
                $state.params.id, {file: $scope.formData.file, batchName: $scope.formData.batchName}
            );
            deferred.resolve({
                batchId: batchId,
                candidates: [1, 2, 3, 4],
                errors: {},
            });
            $scope.$root.$digest();

            expect($scope.pollBatchStatus).toHaveBeenCalledWith(batchId);
            expect($scope.batchSize).toBe(candidates.length);
            expect($scope.uploadStatus).toBe(constants.uploadBatchStatus.IN_PROGRESS);
            expect($scope.count).toBe(0);
            expect($scope.batchId).toBe(batchId);
        });

        it('sets errors in case of validation error', function () {
            var deferred = $q.defer();
            var data = {
                errors: {'batchName': ['This is required']},
            };

            spyOn(api.uploadPlus, 'uploadCsv').and.callFake(function () {
                return deferred.promise;
            });

            $scope.upload();
            deferred.reject(data);
            $scope.$root.$digest();

            expect($scope.errors).toEqual(data.errors);
        });
    });

    describe('pollBatchStatus', function () {
        it('does nothing if polling is not in progress', function () {
            $scope.uploadStatus = null;
            spyOn(api.uploadPlus, 'checkStatus');

            $scope.pollBatchStatus();

            expect(api.uploadPlus.checkStatus).not.toHaveBeenCalled();
        });

        it('stops polling in case of error', function () {
            var deferred = $q.defer();

            spyOn(api.uploadPlus, 'checkStatus').and.callFake(function () {
                return deferred.promise;
            });

            spyOn($interval, 'cancel');

            $scope.uploadStatus = constants.uploadBatchStatus.IN_PROGRESS;
            $scope.pollBatchStatus();

            $interval.flush(1001);
            deferred.reject();
            $scope.$root.$digest();

            expect($scope.uploadStatus).toBe(constants.uploadBatchStatus.FAILED);
            expect($interval.cancel).toHaveBeenCalled();
        });

        it('calls save upload on finished polling', function () {
            var deferred = $q.defer();
            var batchId = 123;

            var statuses = {
                '1': {
                    imageStatus: constants.asyncUploadJobStatus.OK,
                    urlStatus: constants.asyncUploadJobStatus.OK,
                },
                '2': {
                    imageStatus: constants.asyncUploadJobStatus.FAILED,
                    urlStatus: constants.asyncUploadJobStatus.FAILED,
                },
            };

            spyOn(api.uploadPlus, 'checkStatus').and.callFake(function () {
                return deferred.promise;
            });
            spyOn($scope, 'saveUpload');
            spyOn($modalInstance, 'close');
            spyOn($interval, 'cancel');

            $scope.batchSize = 2;
            $scope.candidates = ['1', '2'];
            $scope.uploadStatus = constants.uploadBatchStatus.IN_PROGRESS;
            $scope.pollBatchStatus(batchId);
            $interval.flush(1001);

            expect(api.uploadPlus.checkStatus).toHaveBeenCalledWith(
                $state.params.id, batchId
            );
            deferred.resolve({candidates: statuses});
            $scope.$root.$digest();

            expect($scope.saveUpload).toHaveBeenCalled();
            expect($modalInstance.close).not.toHaveBeenCalled();
            expect($interval.cancel).toHaveBeenCalled();
        });

        it('sets number of errors and error report on saving content ads', function () {
            var deferred = $q.defer();
            var batchId = 123;
            var data = {
                numErrors: 2,
                errorReport: 'http://zemanta.com/error-report',
            };

            spyOn(api.uploadPlus, 'save').and.callFake(function () {
                return deferred.promise;
            });
            spyOn($modalInstance, 'close');

            $scope.batchId = batchId;
            $scope.uploadStatus = constants.uploadBatchStatus.IN_PROGRESS;
            $scope.saveUpload();

            expect(api.uploadPlus.save).toHaveBeenCalledWith(
                $state.params.id, batchId
            );
            deferred.resolve(data);
            $scope.$root.$digest();

            expect($scope.uploadStatus).toBe(constants.uploadBatchStatus.DONE);
            expect($modalInstance.close).not.toHaveBeenCalled();
            expect($scope.numErrors).toEqual(2);
            expect($scope.errorReport).toEqual(data.errorReport);
        });

        it ('sets upload status on cancel', function () {
            var deferred = $q.defer();
            var batchId = 123;
            $scope.batchId = batchId;

            spyOn(api.uploadPlus, 'cancel').and.callFake(function () {
                return deferred.promise;
            });
            spyOn($scope, '$dismiss');

            $scope.uploadStatus = constants.uploadBatchStatus.IN_PROGRESS;
            $scope.cancel();

            expect(api.uploadPlus.cancel).toHaveBeenCalledWith(
                $state.params.id, batchId
            );

            deferred.resolve();
            $scope.$root.$digest();

            expect($scope.$dismiss).not.toHaveBeenCalled();
            expect($scope.uploadStatus, constants.uploadBatchStatus.CANCELLED);
        });
    });
});
