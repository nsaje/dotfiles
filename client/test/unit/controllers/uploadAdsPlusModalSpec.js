// /* globals describe, beforeEach, module, inject, constants, it, spyOn, expect */
// 'use strict';

// describe('UploadAdsPlusModalCtrl', function () {
//     var $scope, $modalInstance, api, $state, $q, $timeout, openedDeferred;

//     beforeEach(module('one'));
//     beforeEach(module('stateMock'));

//     beforeEach(inject(function ($controller, $rootScope, _$q_, _$timeout_, _$state_) {
//         $q = _$q_;
//         $timeout = _$timeout_;
//         $scope = $rootScope.$new();
//         $scope.$dismiss = function () {};

//         openedDeferred = $q.defer();
//         $modalInstance = {
//             close: function () {},
//             opened: openedDeferred.promise,
//         };
//         api = {
//             adGroupAdsUpload: {
//                 upload: function () {},
//                 checkStatus: function () {},
//                 cancel: function () {},
//                 getDefaults: function () {
//                     return {
//                         then: function () {},
//                     };
//                 },
//             },
//         };

//         $scope.user = {
//             timezoneOffset: 0,
//         };

//         $state = _$state_;
//         $state.params = {id: 123};

//         $controller(
//             'UploadAdsPlusModalCtrl',
//             {$scope: $scope, $modalInstance: $modalInstance, api: api, $state: $state, errors: {}}
//         );
//     }));

//     describe('upload', function () {
//         it('calls api and polls for updates on success', function () {
//             var deferred = $q.defer();
//             var batchId = 123;

//             $scope.formData = {
//                 file: 'testfile',
//                 batchName: 'testname',
//             };

//             spyOn(api.adGroupAdsUpload, 'upload').and.callFake(function () {
//                 return deferred.promise;
//             });
//             spyOn($scope, 'pollBatchStatus');

//             $scope.upload();

//             expect(api.adGroupAdsUpload.upload).toHaveBeenCalledWith(
//                 $state.params.id, {file: $scope.formData.file, batchName: $scope.formData.batchName}
//             );
//             deferred.resolve(batchId);
//             $scope.$root.$digest();

//             expect($scope.pollBatchStatus).toHaveBeenCalledWith(batchId);
//             expect($scope.uploadStatus).toBe(constants.uploadBatchStatus.IN_PROGRESS);
//             expect($scope.step).toBe(1);
//             expect($scope.batchId).toBe(batchId);
//         });

//         it('sets errors in case of validation error', function () {
//             var deferred = $q.defer();
//             var data = {
//                 errors: {'batchName': ['This is required']},
//             };

//             spyOn(api.adGroupAdsUpload, 'upload').and.callFake(function () {
//                 return deferred.promise;
//             });

//             $scope.upload();
//             deferred.reject(data);
//             $scope.$root.$digest();

//             expect($scope.errors).toEqual(data.errors);
//         });
//     });

//     describe('pollBatchStatus', function () {
//         it('does nothing if polling is not in progress', function () {
//             $scope.uploadStatus = null;
//             spyOn(api.adGroupAdsUpload, 'checkStatus');

//             $scope.pollBatchStatus();

//             expect(api.adGroupAdsUpload.checkStatus).not.toHaveBeenCalled();
//         });

//         it('stops polling in case of error', function () {
//             var deferred = $q.defer();

//             spyOn(api.adGroupAdsUpload, 'checkStatus').and.callFake(function () {
//                 return deferred.promise;
//             });

//             $scope.uploadStatus = constants.uploadBatchStatus.IN_PROGRESS;
//             $scope.pollBatchStatus();

//             $timeout.flush();
//             deferred.reject();
//             $scope.$root.$digest();

//             expect($scope.uploadStatus).toBe(constants.uploadBatchStatus.FAILED);
//         });

//         it('schedules another poll', function () {
//             var deferred = $q.defer();

//             spyOn(api.adGroupAdsUpload, 'checkStatus').and.callFake(function () {
//                 return deferred.promise;
//             });

//             $scope.uploadStatus = constants.uploadBatchStatus.IN_PROGRESS;
//             $scope.pollBatchStatus();

//             spyOn($scope, 'pollBatchStatus');

//             $timeout.flush();
//             deferred.resolve({status: constants.uploadBatchStatus.IN_PROGRESS});
//             $scope.$root.$digest();

//             expect($scope.pollBatchStatus).toHaveBeenCalled();
//         });

//         it('saves success on success', function () {
//             var deferred = $q.defer();
//             var batchId = 123;

//             spyOn(api.adGroupAdsUpload, 'checkStatus').and.callFake(function () {
//                 return deferred.promise;
//             });
//             spyOn($modalInstance, 'close');
//             $scope.uploadStatus = constants.uploadBatchStatus.IN_PROGRESS;
//             $scope.pollBatchStatus(batchId);
//             $timeout.flush();

//             expect(api.adGroupAdsUpload.checkStatus).toHaveBeenCalledWith(
//                 $state.params.id, batchId
//             );
//             deferred.resolve({status: constants.uploadBatchStatus.DONE});
//             $scope.$root.$digest();

//             expect($scope.uploadStatus).toBe(constants.uploadBatchStatus.DONE);
//             expect($modalInstance.close).not.toHaveBeenCalled();
//         });

//         it('sets errors in case of failed upload', function () {
//             var deferred = $q.defer();
//             var batchId = 123;
//             var data = {
//                 status: 2,
//                 errors: ['some error'],
//             };

//             spyOn(api.adGroupAdsUpload, 'checkStatus').and.callFake(function () {
//                 return deferred.promise;
//             });
//             spyOn($modalInstance, 'close');

//             $scope.uploadStatus = constants.uploadBatchStatus.IN_PROGRESS;
//             $scope.pollBatchStatus(batchId);
//             $timeout.flush();

//             expect(api.adGroupAdsUpload.checkStatus).toHaveBeenCalledWith(
//                 $state.params.id, batchId
//             );
//             deferred.resolve(data);
//             $scope.$root.$digest();

//             expect($scope.uploadStatus).toBe(constants.uploadBatchStatus.FAILED);
//             expect($modalInstance.close).not.toHaveBeenCalled();
//             expect($scope.errors).toEqual(data.errors);
//         });

//         it ('sets errors in case cancel failed', function () {
//             var deferred = $q.defer();
//             var batchId = 123;
//             $scope.batchId = batchId;

//             var data = {
//                 data: {
//                     errors: {
//                         cancel: 'Some message about error',
//                     },
//                 },
//             };

//             spyOn(api.adGroupAdsUpload, 'cancel').and.callFake(function () {
//                 return deferred.promise;
//             });
//             spyOn($scope, '$dismiss');

//             $scope.uploadStatus = constants.uploadBatchStatus.IN_PROGRESS;
//             $scope.cancel();

//             expect(api.adGroupAdsUpload.cancel).toHaveBeenCalledWith(
//                 $state.params.id, batchId
//             );
//             deferred.reject(data);
//             $scope.$root.$digest();

//             expect($scope.$dismiss).not.toHaveBeenCalled();
//             expect($scope.cancelErrors).toEqual(data.data.errors);
//         });

//         it ('sets cancel in progress parameters', function () {
//             var deferred = $q.defer();
//             var batchId = 123;
//             $scope.batchId = batchId;

//             spyOn(api.adGroupAdsUpload, 'cancel').and.callFake(function () {
//                 return deferred.promise;
//             });
//             spyOn($scope, '$dismiss');

//             $scope.uploadStatus = constants.uploadBatchStatus.IN_PROGRESS;
//             $scope.cancel();

//             expect(api.adGroupAdsUpload.cancel).toHaveBeenCalledWith(
//                 $state.params.id, batchId
//             );

//             deferred.resolve();
//             $scope.$root.$digest();

//             expect($scope.$dismiss).not.toHaveBeenCalled();
//             expect($scope.cancelErrors).toBe(null);
//         });

//         it ('close modal when canceling upload that is not in progress', function () {
//             spyOn(api.adGroupAdsUpload, 'cancel');
//             spyOn($scope, '$dismiss');

//             $scope.uploadStatus = constants.uploadBatchStatus.FAILED;
//             $scope.cancel();

//             expect(api.adGroupAdsUpload.cancel).not.toHaveBeenCalled();

//             $scope.$root.$digest();

//             expect($scope.$dismiss).toHaveBeenCalled();
//         });
//     });
// });
