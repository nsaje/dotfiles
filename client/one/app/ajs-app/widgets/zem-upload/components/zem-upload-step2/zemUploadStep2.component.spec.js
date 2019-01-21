describe('ZemUploadStep2Ctrl', function() {
    var scope, $q, ctrl;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(angular.mock.module('stateMock'));

    beforeEach(inject(function($controller, $rootScope, _$q_) {
        $q = _$q_;
        scope = $rootScope.$new();
        var mockEndpoint = {
            upload: function() {},
            checkStatus: function() {},
            updateCandidate: function() {},
            removeCandidate: function() {},
            addCandidate: function() {},
            save: function() {},
            cancel: function() {},
            getVideoAsset: function() {},
        };

        ctrl = $controller(
            'ZemUploadStep2Ctrl',
            {$scope: scope},
            {
                endpoint: mockEndpoint,
                callback: function() {},
                candidates: [
                    {
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
                        imageStatus:
                            constants.asyncUploadJobStatus.WAITING_RESPONSE,
                        urlStatus:
                            constants.asyncUploadJobStatus.WAITING_RESPONSE,
                    },
                ],
                batchId: 1,
                batchName: 'mock batch',
                closeModal: function() {},
            }
        );

        ctrl.adPickerApi.getWaitingCandidateIds = function() {
            return [];
        };
        ctrl.adPickerApi.isVideoAssetBeingProcessed = function() {};
        ctrl.adPickerApi.isVideoAssetProcessingErrorPresent = function() {};
        ctrl.adPickerApi.hasErrors = function() {};
    }));

    describe('upload save', function() {
        beforeEach(function() {
            ctrl.candidates = [
                {
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
                    imageStatus: constants.asyncUploadJobStatus.OK,
                    urlStatus: constants.asyncUploadJobStatus.OK,
                },
            ];
        });

        it('switches to last step on success', function() {
            var deferred = $q.defer();
            spyOn(ctrl.endpoint, 'save').and.callFake(function() {
                return deferred.promise;
            });
            spyOn(ctrl, 'callback').and.stub();

            ctrl.batchId = 1234;
            ctrl.formData.batchName = 'new batch name';

            ctrl.save();
            expect(ctrl.endpoint.save).toHaveBeenCalledWith(
                ctrl.batchId,
                ctrl.formData.batchName
            );
            expect(ctrl.saveRequestInProgress).toBe(true);
            expect(ctrl.saveRequestFailed).toBe(false);

            var numSuccessful = 50;
            deferred.resolve({
                numSuccessful: numSuccessful,
            });
            scope.$digest();

            expect(ctrl.callback).toHaveBeenCalledWith({
                numSuccessful: numSuccessful,
            });
            expect(ctrl.saveRequestInProgress).toBe(false);
            expect(ctrl.saveRequestFailed).toBe(false);
        });

        it('sets a flag on failure', function() {
            var deferred = $q.defer();
            spyOn(ctrl.endpoint, 'save').and.callFake(function() {
                return deferred.promise;
            });
            spyOn(ctrl, 'callback').and.stub();

            ctrl.batchId = 1234;
            ctrl.formData.batchName = 'new batch name';

            ctrl.save();
            expect(ctrl.endpoint.save).toHaveBeenCalledWith(
                ctrl.batchId,
                ctrl.formData.batchName
            );
            expect(ctrl.saveRequestInProgress).toBe(true);
            expect(ctrl.saveRequestFailed).toBe(false);

            deferred.reject({});
            scope.$digest();

            expect(ctrl.callback).not.toHaveBeenCalled();
            expect(ctrl.saveRequestInProgress).toBe(false);
            expect(ctrl.saveRequestFailed).toBe(true);
        });
    });

    describe('upload cancel', function() {
        it('closes the modal window', function() {
            var deferred = $q.defer();
            spyOn(ctrl.endpoint, 'cancel').and.callFake(function() {
                return deferred.promise;
            });
            spyOn(ctrl, 'closeModal');

            ctrl.batchId = 1234;

            ctrl.cancel();
            expect(ctrl.endpoint.cancel).toHaveBeenCalledWith(ctrl.batchId);

            expect(ctrl.closeModal).toHaveBeenCalled();
        });
    });
});
