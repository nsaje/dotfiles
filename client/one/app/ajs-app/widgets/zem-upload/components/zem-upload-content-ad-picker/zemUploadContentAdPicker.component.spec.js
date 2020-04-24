describe('zemUploadContentAdPicker', function() {
    var $rootScope, $injector, $q, $ctrl, $interval;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function(
        $componentController,
        _$rootScope_,
        _$injector_,
        _$q_,
        _$interval_
    ) {
        $rootScope = _$rootScope_;
        $injector = _$injector_;
        $q = _$q_;
        $interval = _$interval_;

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

        var bindings = {
            endpoint: mockEndpoint,
            batchId: 1,
            batchName: 'mock batch',
            candidates: [
                {
                    id: 1,
                    url: 'http://example.com/url1',
                    title: 'Title 1',
                    imageUrl: 'http://exmaple.com/img1.jpg',
                    imageCrop: 'center',
                    iconUrl: 'http://exmaple.com/icon1.jpg',
                    description: '',
                    displayUrl: 'example.com',
                    brandName: '',
                    callToAction: 'Read more',
                    label: 'title1',
                    imageStatus:
                        constants.asyncUploadJobStatus.WAITING_RESPONSE,
                    iconStatus: constants.asyncUploadJobStatus.WAITING_RESPONSE,
                    urlStatus: constants.asyncUploadJobStatus.WAITING_RESPONSE,
                },
            ],
        };
        $ctrl = $componentController('zemUploadContentAdPicker', {}, bindings);
    }));

    describe('status polling', function() {
        var candidates;
        beforeEach(function() {
            candidates = [
                {
                    id: 1,
                    url: 'http://example.com/url1',
                    title: 'Title 1',
                    imageUrl: 'http://exmaple.com/img1.jpg',
                    imageCrop: 'center',
                    iconUrl: 'http://exmaple.com/icon1.jpg',
                    description: '',
                    displayUrl: 'example.com',
                    brandName: '',
                    callToAction: 'Read more',
                    label: 'title1',
                    imageStatus:
                        constants.asyncUploadJobStatus.WAITING_RESPONSE,
                    iconStatus: constants.asyncUploadJobStatus.WAITING_RESPONSE,
                    urlStatus: constants.asyncUploadJobStatus.WAITING_RESPONSE,
                    primaryTrackerUrlStatus:
                        constants.asyncUploadJobStatus.WAITING_RESPONSE,
                    secondaryTrackerUrlStatus:
                        constants.asyncUploadJobStatus.WAITING_RESPONSE,
                    errors: {},
                },
            ];
        });

        it('partially updates candidates on success', function() {
            $ctrl.candidates = angular.copy(candidates);

            var deferred = $q.defer();
            spyOn($ctrl.endpoint, 'checkStatus').and.callFake(function() {
                return deferred.promise;
            });
            spyOn($interval, 'cancel');
            $ctrl.$onInit();
            $interval.flush(2501);

            var resolvedCandidate = {
                id: 1,
                url: 'http://example.com/url1',
                title: '',
                imageUrl: 'http://exmaple.com/img1.jpg',
                imageCrop: 'center',
                iconUrl: 'http://exmaple.com/icon1.jpg',
                description: '',
                displayUrl: 'example.com',
                brandName: '',
                callToAction: 'Read more',
                label: 'title1',
                hostedImageUrl: 'http://zemanta.com/img1.jpg',
                landscapeHostedImageUrl: 'http://zemanta.com/img1.jpg',
                hostedIconUrl: 'http://zemanta.com/icon1.jpg',
                imageStatus: constants.asyncUploadJobStatus.OK,
                iconStatus: constants.asyncUploadJobStatus.OK,
                urlStatus: constants.asyncUploadJobStatus.FAILED,
                primaryTrackerUrlStatus:
                    constants.asyncUploadJobStatus.WAITING_RESPONSE,
                secondaryTrackerUrlStatus:
                    constants.asyncUploadJobStatus.WAITING_RESPONSE,
                errors: {
                    url: ['Invalid URL'],
                    description: ['Missing description'],
                    title: ['Invalid title'],
                },
            };
            deferred.resolve({
                candidates: [resolvedCandidate],
            });
            $rootScope.$digest();

            expect($ctrl.candidates).toEqual([resolvedCandidate]);
            expect($ctrl.candidates[0].title).toEqual('');
            expect($ctrl.candidates[0].imageStatus).toEqual(
                constants.asyncUploadJobStatus.OK
            );
            expect($ctrl.candidates[0].iconStatus).toEqual(
                constants.asyncUploadJobStatus.OK
            );
            expect($ctrl.candidates[0].urlStatus).toEqual(
                constants.asyncUploadJobStatus.FAILED
            );
            expect($ctrl.candidates[0].hostedImageUrl).toBe(
                'http://zemanta.com/img1.jpg'
            );
            expect($ctrl.candidates[0].hostedIconUrl).toBe(
                'http://zemanta.com/icon1.jpg'
            );
            expect($ctrl.candidates[0].landscapeHostedImageUrl).toBe(
                'http://zemanta.com/img1.jpg'
            );
            expect($ctrl.candidates[0].errors.title).toEqual(['Invalid title']);
            expect($ctrl.candidates[0].errors.url).toEqual(['Invalid URL']);

            $interval.flush(2500);
            $rootScope.$digest();
        });

        it('does nothing on failure', function() {
            $ctrl.candidates = angular.copy(candidates);

            var deferred = $q.defer();
            spyOn($ctrl.endpoint, 'checkStatus').and.callFake(function() {
                return deferred.promise;
            });
            $ctrl.$onInit();
            $interval.flush(2501);

            deferred.reject();
            $rootScope.$digest();

            expect($ctrl.candidates).toEqual(candidates);
            expect($ctrl.pollInterval).not.toBeNull();

            $interval.flush(2501);
            $rootScope.$digest();

            expect($ctrl.pollInterval).not.toBeNull();
        });

        it('polls only for candidates that are waiting', function() {
            $ctrl.candidates = angular.copy(candidates);
            $ctrl.candidates.push({
                id: 2,
                url: 'http://example.com/url2',
                title: 'Title 2',
                imageUrl: 'http://exmaple.com/img2.jpg',
                imageCrop: 'center',
                iconUrl: 'http://exmaple.com/icon2.jpg',
                description: '',
                displayUrl: 'example.com',
                brandName: '',
                callToAction: 'Read more',
                label: 'title2',
                imageStatus: constants.asyncUploadJobStatus.OK,
                iconStatus: constants.asyncUploadJobStatus.OK,
                urlStatus: constants.asyncUploadJobStatus.OK,
            });
            $ctrl.batchId = 1234;

            var deferred = $q.defer();
            spyOn($ctrl.endpoint, 'checkStatus').and.callFake(function() {
                return deferred.promise;
            });
            $ctrl.$onInit();
            $interval.flush(2501);

            expect(
                $ctrl.endpoint.checkStatus
            ).toHaveBeenCalledWith($ctrl.batchId, [1]);
        });

        it('stops polling when no candidates are left waiting', function() {
            $ctrl.candidates = angular.copy(candidates);

            var deferred = $q.defer();
            spyOn($ctrl.endpoint, 'checkStatus').and.callFake(function() {
                return deferred.promise;
            });
            spyOn($interval, 'cancel');
            $ctrl.$onInit();
            $interval.flush(2501);

            var resolvedCandidate = {
                id: 1,
                url: 'http://example.com/url1',
                title: 'Title 1',
                imageUrl: 'http://exmaple.com/img1.jpg',
                imageCrop: 'center',
                iconUrl: 'http://exmaple.com/icon1.jpg',
                description: '',
                displayUrl: 'example.com',
                brandName: '',
                callToAction: 'Read more',
                label: 'title1',
                imageStatus: constants.asyncUploadJobStatus.OK,
                iconStatus: constants.asyncUploadJobStatus.OK,
                urlStatus: constants.asyncUploadJobStatus.OK,
                errors: {
                    imageUrl: ['Invalid image URL'],
                    description: ['Missing description'],
                },
            };
            deferred.resolve({
                candidates: [resolvedCandidate],
            });

            $rootScope.$digest();
            expect($ctrl.candidates[0].imageStatus).toEqual(
                resolvedCandidate.imageStatus
            );
            expect($ctrl.candidates[0].iconStatus).toEqual(
                resolvedCandidate.iconStatus
            );
            expect($ctrl.candidates[0].urlStatus).toEqual(
                resolvedCandidate.urlStatus
            );
            expect($interval.cancel).not.toHaveBeenCalled();

            $interval.flush(2500);
            expect($interval.cancel).toHaveBeenCalled();
        });
    });

    describe('candidate addition', function() {
        it('adds new candidate and opens edit form on success', function() {
            $ctrl.candidates = [];
            $ctrl.editFormApi = {
                open: function() {},
            };
            $ctrl.batchId = 1234;

            var deferred = $q.defer();
            spyOn($ctrl.endpoint, 'addCandidate').and.callFake(function() {
                return deferred.promise;
            });
            spyOn($ctrl.editFormApi, 'open').and.stub();

            expect($ctrl.addCandidateRequestInProgress).toBeUndefined();
            expect($ctrl.addCandidateRequestFailed).toBeUndefined();

            $ctrl.addCandidate();
            expect($ctrl.addCandidateRequestInProgress).toBe(true);
            expect($ctrl.addCandidateRequestFailed).toBe(false);

            var returnedCandidate = {
                id: 1,
                url: 'http://example.com/url1',
                title: 'Title 1',
                imageUrl: 'http://exmaple.com/img1.jpg',
                imageCrop: 'center',
                iconUrl: 'http://exmaple.com/icon1.jpg',
                description: '',
                displayUrl: 'example.com',
                brandName: '',
                callToAction: 'Read more',
                label: 'title1',
                imageStatus: constants.asyncUploadJobStatus.WAITING_RESPONSE,
                iconStatus: constants.asyncUploadJobStatus.WAITING_RESPONSE,
                urlStatus: constants.asyncUploadJobStatus.WAITING_RESPONSE,
                primaryTrackerUrlStatus:
                    constants.asyncUploadJobStatus.WAITING_RESPONSE,
                secondaryTrackerUrlStatus:
                    constants.asyncUploadJobStatus.WAITING_RESPONSE,
            };
            deferred.resolve({
                candidate: returnedCandidate,
            });
            $rootScope.$digest();

            expect($ctrl.candidates).toEqual([returnedCandidate]);
            expect($ctrl.editFormApi.open).toHaveBeenCalledWith(
                returnedCandidate
            );
            expect($ctrl.addCandidateRequestInProgress).toBe(false);
            expect($ctrl.addCandidateRequestFailed).toBe(false);
        });

        it('sets a flag on failure', function() {
            $ctrl.candidates = [];
            $ctrl.editFormApi = {
                open: function() {},
            };
            $ctrl.batchId = 1234;

            var deferred = $q.defer();
            spyOn($ctrl.endpoint, 'addCandidate').and.callFake(function() {
                return deferred.promise;
            });
            spyOn($ctrl.editFormApi, 'open').and.stub();

            expect($ctrl.addCandidateRequestInProgress).toBeUndefined();
            expect($ctrl.addCandidateRequestFailed).toBeUndefined();

            $ctrl.addCandidate();
            expect($ctrl.addCandidateRequestInProgress).toBe(true);
            expect($ctrl.addCandidateRequestFailed).toBe(false);

            deferred.reject();
            $rootScope.$digest();

            expect($ctrl.candidates).toEqual([]);
            expect($ctrl.editFormApi.open).not.toHaveBeenCalled();
            expect($ctrl.addCandidateRequestInProgress).toBe(false);
            expect($ctrl.addCandidateRequestFailed).toBe(true);
        });
    });

    describe('candidate removal', function() {
        it('removes candidate on success', function() {
            var candidate = {
                id: 1,
                url: 'http://example.com/url1',
                title: 'Title 1',
                imageUrl: 'http://exmaple.com/img1.jpg',
                imageCrop: 'center',
                iconUrl: 'http://exmaple.com/icon1.jpg',
                description: '',
                displayUrl: 'example.com',
                brandName: '',
                callToAction: 'Read more',
                label: 'title1',
                imageStatus: constants.asyncUploadJobStatus.WAITING_RESPONSE,
                iconStatus: constants.asyncUploadJobStatus.WAITING_RESPONSE,
                urlStatus: constants.asyncUploadJobStatus.WAITING_RESPONSE,
            };
            $ctrl.candidates = [candidate];
            $ctrl.batchId = 1234;

            var deferred = $q.defer();
            spyOn($ctrl.endpoint, 'removeCandidate').and.callFake(function() {
                return deferred.promise;
            });

            var mockEvent = {
                stopPropagation: function() {},
            };
            spyOn(mockEvent, 'stopPropagation');
            $ctrl.removeCandidate(candidate, mockEvent);
            expect(mockEvent.stopPropagation).toHaveBeenCalled();
            expect($ctrl.endpoint.removeCandidate).toHaveBeenCalledWith(
                candidate.id,
                $ctrl.batchId
            );
            expect(candidate.removeRequestInProgress).toBe(true);
            expect(candidate.removeRequestFailed).toBe(false);

            deferred.resolve();
            $rootScope.$digest();

            expect($ctrl.candidates).toEqual([]);
        });

        it('sets a flag on failure', function() {
            var candidate = {
                id: 1,
                url: 'http://example.com/url1',
                title: 'Title 1',
                imageUrl: 'http://exmaple.com/img1.jpg',
                imageCrop: 'center',
                iconUrl: 'http://exmaple.com/icon1.jpg',
                description: '',
                displayUrl: 'example.com',
                brandName: '',
                callToAction: 'Read more',
                label: 'title1',
                imageStatus: constants.asyncUploadJobStatus.WAITING_RESPONSE,
                iconStatus: constants.asyncUploadJobStatus.WAITING_RESPONSE,
                urlStatus: constants.asyncUploadJobStatus.WAITING_RESPONSE,
            };
            $ctrl.candidates = [candidate];
            $ctrl.batchId = 1234;

            var deferred = $q.defer();
            spyOn($ctrl.endpoint, 'removeCandidate').and.callFake(function() {
                return deferred.promise;
            });

            var mockEvent = {
                stopPropagation: function() {},
            };
            spyOn(mockEvent, 'stopPropagation');
            $ctrl.removeCandidate(candidate, mockEvent);
            expect(mockEvent.stopPropagation).toHaveBeenCalled();
            expect($ctrl.endpoint.removeCandidate).toHaveBeenCalledWith(
                candidate.id,
                $ctrl.batchId
            );
            expect(candidate.removeRequestInProgress).toBe(true);
            expect(candidate.removeRequestFailed).toBe(false);

            deferred.reject();
            $rootScope.$digest();

            expect(candidate.removeRequestInProgress).toBe(false);
            expect(candidate.removeRequestFailed).toBe(true);
            expect($ctrl.candidates.length).toEqual(1);
        });
    });

    describe('video uploader', function() {
        var candidate;

        beforeEach(function() {
            spyOn($ctrl.endpoint, 'checkStatus').and.callFake(
                zemSpecsHelper.getMockedAsyncFunction($injector, {})
            );
            candidate = {
                videoAsset: {id: 1},
            };
        });

        it('keeps polling if video asset is being uploaded', function() {
            spyOn($ctrl.endpoint, 'getVideoAsset').and.callFake(
                zemSpecsHelper.getMockedAsyncFunction($injector, {
                    status: constants.videoAssetStatus.NOT_UPLOADED,
                })
            );

            $ctrl.startPollingVideoAssetStatus(candidate);
            $interval.flush(7000);
            expect($ctrl.endpoint.getVideoAsset).toHaveBeenCalledTimes(3);
        });

        it('keeps polling if video asset is being processed', function() {
            spyOn($ctrl.endpoint, 'getVideoAsset').and.callFake(
                zemSpecsHelper.getMockedAsyncFunction($injector, {
                    status: constants.videoAssetStatus.PROCESSING,
                })
            );

            $ctrl.startPollingVideoAssetStatus(candidate);
            $interval.flush(7000);
            expect($ctrl.endpoint.getVideoAsset).toHaveBeenCalledTimes(3);
        });

        it('stops polling if video asset is ready for use', function() {
            spyOn($ctrl.endpoint, 'getVideoAsset').and.callFake(
                zemSpecsHelper.getMockedAsyncFunction($injector, {
                    status: constants.videoAssetStatus.READY_FOR_USE,
                })
            );

            $ctrl.startPollingVideoAssetStatus(candidate);
            $interval.flush(7000);
            expect($ctrl.endpoint.getVideoAsset).toHaveBeenCalledTimes(1);
        });

        it('stops polling if video asset processing error', function() {
            spyOn($ctrl.endpoint, 'getVideoAsset').and.callFake(
                zemSpecsHelper.getMockedAsyncFunction($injector, {
                    status: constants.videoAssetStatus.PROCESSING_ERROR,
                })
            );

            $ctrl.startPollingVideoAssetStatus(candidate);
            $interval.flush(7000);
            expect($ctrl.endpoint.getVideoAsset).toHaveBeenCalledTimes(1);
        });

        it('stops polling if modal is closed', function() {
            spyOn($ctrl.endpoint, 'getVideoAsset').and.callFake(
                zemSpecsHelper.getMockedAsyncFunction($injector, {
                    status: constants.videoAssetStatus.PROCESSING,
                })
            );

            $ctrl.candidates = [candidate];
            $ctrl.startPollingVideoAssetStatus(candidate);
            $interval.flush(4000);
            $rootScope.$destroy();
            $interval.flush(3000);
            expect($ctrl.endpoint.getVideoAsset).toHaveBeenCalledTimes(2);
        });
    });
});
