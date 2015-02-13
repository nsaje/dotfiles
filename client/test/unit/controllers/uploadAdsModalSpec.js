'use strict'

describe('UploadAdsModalCtrl', function() {
    var $scope, $modalInstance, api, $state, $q;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(inject(function($controller, $rootScope, _$q_) {
        $q = _$q_;
        $scope = $rootScope.$new();
        $modalInstance = {close: function(){}};
        api = {adGroupAdsPlusUpload: {upload: function() {}}};
        $state = {params: {id: 123}};

        $controller(
            'UploadAdsModalCtrl',
            {$scope: $scope, $modalInstance: $modalInstance, api: api, $state: $state}
        );
    }));

    describe('upload', function() {
        it('calls api and closes dialog on success', function() {
            var deferred = $q.defer();

            $scope.formData = {
                file: 'testfile',
                batchName: 'testname'
            };

            spyOn(api.adGroupAdsPlusUpload, 'upload').and.callFake(function() {
                return deferred.promise;
            });
            spyOn($modalInstance, 'close');

            $scope.upload();
            deferred.resolve();
            $scope.$root.$digest();

            expect(api.adGroupAdsPlusUpload.upload).toHaveBeenCalledWith(
                $state.params.id, $scope.formData.file, $scope.formData.batchName
            );
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
