'use strict'

describe('UploadAdsModalCtrl', function() {
    var $scope, $modalInstance, api, $state, $q, $timeout;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(inject(function($controller, $rootScope, _$q_, _$timeout_) {
        $q = _$q_;
        $timeout = _$timeout_;
        $scope = $rootScope.$new();
        $modalInstance = {close: function(){}};
        api = {adGroupAdsPlusUpload: {upload: function() {}, checkStatus: function() {}}};
        $state = {params: {id: 123}};

        $controller(
            'UploadAdsModalCtrl',
            {$scope: $scope, $modalInstance: $modalInstance, api: api, $state: $state}
        );
    }));

    describe('upload', function() {
        it('calls api, checks status and closes dialog on success', function() {
            var uploadDeferred = $q.defer();
            var checkStatusDeferred = $q.defer();
            var batchId = 123;

            $scope.formData = {
                file: 'testfile',
                batchName: 'testname'
            };

            spyOn(api.adGroupAdsPlusUpload, 'upload').and.callFake(function() {
                return uploadDeferred.promise;
            });
            spyOn(api.adGroupAdsPlusUpload, 'checkStatus').and.callFake(function() {
                return checkStatusDeferred.promise;
            });
            spyOn($modalInstance, 'close');

            $scope.upload();

            expect(api.adGroupAdsPlusUpload.upload).toHaveBeenCalledWith(
                $state.params.id, $scope.formData.file, $scope.formData.batchName
            );
            uploadDeferred.resolve(batchId);
            $scope.$root.$digest();

            expect($scope.isInProgress).toBe(true);

            $timeout.flush();

            expect(api.adGroupAdsPlusUpload.checkStatus).toHaveBeenCalledWith(
                $state.params.id, batchId
            );
            checkStatusDeferred.resolve({status: 1});
            $scope.$root.$digest();

            expect($scope.isInProgress).toBe(false);
            expect($modalInstance.close).toHaveBeenCalled();
        });

        it('sets errors in case of validation error', function() {
            var deferred = $q.defer();
            var errors = {'batchName': ['This is required']};

            spyOn(api.adGroupAdsPlusUpload, 'upload').and.callFake(function() {
                return deferred.promise;
            });
            
            $scope.upload();
            deferred.reject(errors);
            $scope.$root.$digest();

            expect($scope.errors).toEqual(errors);
        });
    });
});
