'use strict';

describe('UploadAdsModalCtrl', function () {
    var $scope, $modalInstance, api, $state, $q, $timeout, openedDeferred;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(inject(function ($controller, $rootScope, _$q_, _$timeout_, _$state_) {
        $q = _$q_;
        $timeout = _$timeout_;
        $scope = $rootScope.$new();

        openedDeferred = $q.defer();
        $modalInstance = {
            close: function () {},
            opened: openedDeferred.promise
        };
        api = {
            adGroupAdsPlusUpload: {
                upload: function () {},
                checkStatus: function () {},
                getDefaults: function () {
                    return {
                        then: function () {}
                    };
                }
            }
        };

        $scope.user = {
            timezoneOffset: 0
        };

        $state = _$state_;
        $state.params = {id: 123};

        $controller(
            'UploadAdsModalCtrl',
            {$scope: $scope, $modalInstance: $modalInstance, api: api, $state: $state, errors: {}}
        );
    }));

    describe('upload', function () {
        it('calls api and polls for updates on success', function () {
            var deferred = $q.defer();
            var batchId = 123;

            $scope.formData = {
                file: 'testfile',
                batchName: 'testname'
            };

            spyOn(api.adGroupAdsPlusUpload, 'upload').and.callFake(function () {
                return deferred.promise;
            });
            spyOn($scope, 'pollBatchStatus');

            $scope.upload();

            expect(api.adGroupAdsPlusUpload.upload).toHaveBeenCalledWith(
                $state.params.id, {file: $scope.formData.file, batchName: $scope.formData.batchName}
            );
            deferred.resolve(batchId);
            $scope.$root.$digest();

            expect($scope.pollBatchStatus).toHaveBeenCalledWith(batchId);
            expect($scope.isInProgress).toBe(true);
        });

        it('sets errors in case of validation error', function () {
            var deferred = $q.defer();
            var data = {
                errors: {'batchName': ['This is required']},
            };

            spyOn(api.adGroupAdsPlusUpload, 'upload').and.callFake(function () {
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
            $scope.isInProgress = false;
            spyOn(api.adGroupAdsPlusUpload, 'checkStatus');

            $scope.pollBatchStatus();

            expect(api.adGroupAdsPlusUpload.checkStatus).not.toHaveBeenCalled();
        });

        it('stops polling in case of error', function () {
            var deferred = $q.defer();

            spyOn(api.adGroupAdsPlusUpload, 'checkStatus').and.callFake(function () {
                return deferred.promise;
            });

            $scope.isInProgress = true;

            $scope.pollBatchStatus();

            $timeout.flush();
            deferred.reject();
            $scope.$root.$digest();

            expect($scope.isInProgress).toBe(false);
        });

        it('schedules another poll', function () {
            var deferred = $q.defer();

            spyOn(api.adGroupAdsPlusUpload, 'checkStatus').and.callFake(function () {
                return deferred.promise;
            });

            $scope.isInProgress = true;

            $scope.pollBatchStatus();

            spyOn($scope, 'pollBatchStatus');

            $timeout.flush();
            deferred.resolve({status: 3});
            $scope.$root.$digest();

            expect($scope.pollBatchStatus).toHaveBeenCalled();
        });

        it('closes dialog on success', function () {
            var deferred = $q.defer();
            var batchId = 123;

            spyOn(api.adGroupAdsPlusUpload, 'checkStatus').and.callFake(function () {
                return deferred.promise;
            });
            spyOn($modalInstance, 'close');

            $scope.isInProgress = true;

            $scope.pollBatchStatus(batchId);
            $timeout.flush();

            expect(api.adGroupAdsPlusUpload.checkStatus).toHaveBeenCalledWith(
                $state.params.id, batchId
            );
            deferred.resolve({status: 1});
            $scope.$root.$digest();

            expect($scope.isInProgress).toBe(false);
            expect($modalInstance.close).toHaveBeenCalled();
        });

        it('sets errors in case of failed upload', function () {
            var deferred = $q.defer();
            var batchId = 123;
            var data = {
                status: 2,
                errors: ['some error']
            };

            spyOn(api.adGroupAdsPlusUpload, 'checkStatus').and.callFake(function () {
                return deferred.promise;
            });
            spyOn($modalInstance, 'close');

            $scope.isInProgress = true;

            $scope.pollBatchStatus(batchId);
            $timeout.flush();

            expect(api.adGroupAdsPlusUpload.checkStatus).toHaveBeenCalledWith(
                $state.params.id, batchId
            );
            deferred.resolve(data);
            $scope.$root.$digest();

            expect($scope.isInProgress).toBe(false);
            expect($modalInstance.close).not.toHaveBeenCalled();
            expect($scope.errors).toEqual(data.errors);
        });
    });
});
