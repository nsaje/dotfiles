/* globals describe, beforeEach, module, inject, it, expect, constants, angular, spyOn */
'use strict';

describe('ZemUploadStep2Ctrl', function () {
    var scope, $q, ctrl, $interval;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(inject(function ($controller, $rootScope, _$q_, _$interval_) {
        $q = _$q_;
        $interval = _$interval_;
        scope = $rootScope.$new();
        var mockEndpoint = {
            upload: function () {},
            checkStatus: function () {},
            updateCandidate: function () {},
            removeCandidate: function () {},
            addCandidate: function () {},
            save: function () {},
            cancel: function () {},
        };

        ctrl = $controller(
            'ZemUploadStep2Ctrl',
            {$scope: scope},
            {
                endpoint: mockEndpoint,
                callback: function () {},
                candidates: [{
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
                }],
                batchId: 1,
                batchName: 'mock batch',
                closeModal: function () {},
                hasPermission: function () { return false; },
            }
        );
    }));

    describe('status polling', function () {
        var candidates;
        beforeEach(function () {
            candidates = [{
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
                errors: {},
            }];
        });

        it('updates candidates on success', function () {
            ctrl.candidates = angular.copy(candidates);

            var deferred = $q.defer();
            spyOn(ctrl.endpoint, 'checkStatus').and.callFake(function () {
                return deferred.promise;
            });
            spyOn($interval, 'cancel');
            ctrl.startPolling();
            $interval.flush(2501);

            var resolvedCandidate = {
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
                errors: {
                    imageUrl: ['Invalid image URL'],
                    description: ['Missing description'],
                },
            };
            deferred.resolve({
                candidates: [resolvedCandidate],
            });
            scope.$digest();

            expect(ctrl.candidates).toEqual([resolvedCandidate]);
            expect($interval.cancel).not.toHaveBeenCalled();

            $interval.flush(2500);
            scope.$digest();

            expect($interval.cancel).toHaveBeenCalled();
            expect(ctrl.pollInterval).toBeNull();
        });

        it('partially updates candidates on success if user has permission', function () {
            ctrl.candidates = angular.copy(candidates);
            ctrl.hasPermission = function () { return true; };

            var deferred = $q.defer();
            spyOn(ctrl.endpoint, 'checkStatus').and.callFake(function () {
                return deferred.promise;
            });
            spyOn($interval, 'cancel');
            ctrl.startPolling();
            $interval.flush(2501);

            var resolvedCandidate = {
                id: 1,
                url: 'http://example.com/url1',
                title: '',
                imageUrl: 'http://exmaple.com/img1.jpg',
                imageCrop: 'center',
                description: '',
                displayUrl: 'example.com',
                brandName: '',
                callToAction: 'Read more',
                label: 'title1',
                hostedImageUrl: 'http://zemanta.com/img1.jpg',
                imageStatus: constants.asyncUploadJobStatus.OK,
                urlStatus: constants.asyncUploadJobStatus.FAILED,
                errors: {
                    url: ['Invalid URL'],
                    description: ['Missing description'],
                    title: ['Invalid title'],
                },
            };
            deferred.resolve({
                candidates: [resolvedCandidate],
            });
            scope.$digest();

            expect(ctrl.candidates).not.toEqual([resolvedCandidate]);
            expect(ctrl.candidates[0].title).toEqual('Title 1');
            expect(ctrl.candidates[0].imageStatus).toEqual(constants.asyncUploadJobStatus.OK);
            expect(ctrl.candidates[0].urlStatus).toEqual(constants.asyncUploadJobStatus.FAILED);
            expect(ctrl.candidates[0].hostedImageUrl).toBe('http://zemanta.com/img1.jpg');
            expect(ctrl.candidates[0].errors.title).toBeUndefined();
            expect(ctrl.candidates[0].errors.url).toEqual(['Invalid URL']);

            $interval.flush(2500);
            scope.$digest();
        });

        it('does nothing on failure', function () {
            ctrl.candidates = angular.copy(candidates);

            var deferred = $q.defer();
            spyOn(ctrl.endpoint, 'checkStatus').and.callFake(function () {
                return deferred.promise;
            });
            ctrl.startPolling();
            $interval.flush(2501);

            deferred.reject();
            scope.$digest();

            expect(ctrl.candidates).toEqual(candidates);
            expect(ctrl.pollInterval).not.toBeNull();

            $interval.flush(2501);
            scope.$digest();

            expect(ctrl.pollInterval).not.toBeNull();
        });


        it('polls only for candidates that are waiting', function () {
            ctrl.candidates = angular.copy(candidates);
            ctrl.candidates.push({
                id: 2,
                url: 'http://example.com/url2',
                title: 'Title 2',
                imageUrl: 'http://exmaple.com/img2.jpg',
                imageCrop: 'center',
                description: '',
                displayUrl: 'example.com',
                brandName: '',
                callToAction: 'Read more',
                label: 'title2',
                imageStatus: constants.asyncUploadJobStatus.OK,
                urlStatus: constants.asyncUploadJobStatus.OK,
            });
            ctrl.batchId = 1234;

            var deferred = $q.defer();
            spyOn(ctrl.endpoint, 'checkStatus').and.callFake(function () {
                return deferred.promise;
            });
            ctrl.startPolling();
            $interval.flush(2501);

            expect(ctrl.endpoint.checkStatus).toHaveBeenCalledWith(ctrl.batchId, [1]);
        });

        it('stops polling when no candidates are left waiting', function () {
            ctrl.candidates = angular.copy(candidates);

            var deferred = $q.defer();
            spyOn(ctrl.endpoint, 'checkStatus').and.callFake(function () {
                return deferred.promise;
            });
            spyOn($interval, 'cancel');
            ctrl.startPolling();
            $interval.flush(2501);

            var resolvedCandidate = {
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
                errors: {
                    imageUrl: ['Invalid image URL'],
                    description: ['Missing description'],
                },
            };
            deferred.resolve({
                candidates: [resolvedCandidate],
            });

            scope.$digest();
            expect(ctrl.candidates).toEqual([resolvedCandidate]);
            expect($interval.cancel).not.toHaveBeenCalled();

            $interval.flush(2500);
            expect($interval.cancel).toHaveBeenCalled();
        });
    });

    describe('candidate addition', function () {
        it('adds new candidate and opens edit form on success', function () {
            ctrl.candidates = [];
            ctrl.editFormApi = {
                open: function () {},
            };
            ctrl.batchId = 1234;

            var deferred = $q.defer();
            spyOn(ctrl.endpoint, 'addCandidate').and.callFake(function () {
                return deferred.promise;
            });
            spyOn(ctrl.editFormApi, 'open').and.stub();

            expect(ctrl.addCandidateRequestInProgress).toBeUndefined();
            expect(ctrl.addCandidateRequestFailed).toBeUndefined();

            ctrl.addCandidate();
            expect(ctrl.addCandidateRequestInProgress).toBe(true);
            expect(ctrl.addCandidateRequestFailed).toBe(false);

            var returnedCandidate = {
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
            };
            deferred.resolve({
                candidate: returnedCandidate,
            });
            scope.$digest();

            expect(ctrl.candidates).toEqual([returnedCandidate]);
            expect(ctrl.editFormApi.open).toHaveBeenCalledWith(returnedCandidate);
            expect(ctrl.addCandidateRequestInProgress).toBe(false);
            expect(ctrl.addCandidateRequestFailed).toBe(false);
        });

        it('sets a flag on failure', function () {
            ctrl.candidates = [];
            ctrl.editFormApi = {
                open: function () {},
            };
            ctrl.batchId = 1234;

            var deferred = $q.defer();
            spyOn(ctrl.endpoint, 'addCandidate').and.callFake(function () {
                return deferred.promise;
            });
            spyOn(ctrl.editFormApi, 'open').and.stub();

            expect(ctrl.addCandidateRequestInProgress).toBeUndefined();
            expect(ctrl.addCandidateRequestFailed).toBeUndefined();

            ctrl.addCandidate();
            expect(ctrl.addCandidateRequestInProgress).toBe(true);
            expect(ctrl.addCandidateRequestFailed).toBe(false);

            deferred.reject();
            scope.$digest();

            expect(ctrl.candidates).toEqual([]);
            expect(ctrl.editFormApi.open).not.toHaveBeenCalled();
            expect(ctrl.addCandidateRequestInProgress).toBe(false);
            expect(ctrl.addCandidateRequestFailed).toBe(true);
        });
    });

    describe('candidate removal', function () {
        it('removes candidate on success', function () {
            var candidate = {
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
            };
            ctrl.candidates = [candidate];
            ctrl.batchId = 1234;

            var deferred = $q.defer();
            spyOn(ctrl.endpoint, 'removeCandidate').and.callFake(function () {
                return deferred.promise;
            });

            var mockEvent = {
                stopPropagation: function () {},
            };
            spyOn(mockEvent, 'stopPropagation');
            ctrl.removeCandidate(candidate, mockEvent);
            expect(mockEvent.stopPropagation).toHaveBeenCalled();
            expect(ctrl.endpoint.removeCandidate).toHaveBeenCalledWith(
                candidate.id, ctrl.batchId);
            expect(candidate.removeRequestInProgress).toBe(true);
            expect(candidate.removeRequestFailed).toBe(false);

            deferred.resolve();
            scope.$digest();

            expect(ctrl.candidates).toEqual([]);
        });

        it('sets a flag on failure', function () {
            var candidate = {
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
            };
            ctrl.candidates = [candidate];
            ctrl.batchId = 1234;

            var deferred = $q.defer();
            spyOn(ctrl.endpoint, 'removeCandidate').and.callFake(function () {
                return deferred.promise;
            });

            var mockEvent = {
                stopPropagation: function () {},
            };
            spyOn(mockEvent, 'stopPropagation');
            ctrl.removeCandidate(candidate, mockEvent);
            expect(mockEvent.stopPropagation).toHaveBeenCalled();
            expect(ctrl.endpoint.removeCandidate).toHaveBeenCalledWith(
                candidate.id, ctrl.batchId);
            expect(candidate.removeRequestInProgress).toBe(true);
            expect(candidate.removeRequestFailed).toBe(false);

            deferred.reject();
            scope.$digest();

            expect(candidate.removeRequestInProgress).toBe(false);
            expect(candidate.removeRequestFailed).toBe(true);
            expect(ctrl.candidates.length).toEqual(1);
        });
    });

    describe('upload save', function () {
        beforeEach(function () {
            ctrl.candidates = [{
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
            }];
        });

        it('switches to last step on success', function () {
            var deferred = $q.defer();
            spyOn(ctrl.endpoint, 'save').and.callFake(function () {
                return deferred.promise;
            });
            spyOn(ctrl, 'callback').and.stub();

            ctrl.batchId = 1234;
            ctrl.formData.batchName = 'new batch name';

            ctrl.save();
            expect(ctrl.endpoint.save).toHaveBeenCalledWith(
                ctrl.batchId, ctrl.formData.batchName);
            expect(ctrl.saveRequestInProgress).toBe(true);
            expect(ctrl.saveRequestFailed).toBe(false);

            var numSuccessful = 50;
            deferred.resolve({
                numSuccessful: numSuccessful,
            });
            scope.$digest();

            expect(ctrl.callback).toHaveBeenCalledWith({numSuccessful: numSuccessful});
            expect(ctrl.saveRequestInProgress).toBe(false);
            expect(ctrl.saveRequestFailed).toBe(false);
        });

        it('sets a flag on failure', function () {
            var deferred = $q.defer();
            spyOn(ctrl.endpoint, 'save').and.callFake(function () {
                return deferred.promise;
            });
            spyOn(ctrl, 'callback').and.stub();

            ctrl.batchId = 1234;
            ctrl.formData.batchName = 'new batch name';

            ctrl.save();
            expect(ctrl.endpoint.save).toHaveBeenCalledWith(
                ctrl.batchId, ctrl.formData.batchName);
            expect(ctrl.saveRequestInProgress).toBe(true);
            expect(ctrl.saveRequestFailed).toBe(false);

            deferred.reject({});
            scope.$digest();

            expect(ctrl.callback).not.toHaveBeenCalled();
            expect(ctrl.saveRequestInProgress).toBe(false);
            expect(ctrl.saveRequestFailed).toBe(true);
        });
    });

    describe('upload cancel', function () {
        it('closes the modal window', function () {
            var deferred = $q.defer();
            spyOn(ctrl.endpoint, 'cancel').and.callFake(function () {
                return deferred.promise;
            });
            spyOn(ctrl, 'stopPolling').and.stub();
            spyOn(ctrl, 'closeModal');

            ctrl.batchId = 1234;

            ctrl.cancel();
            expect(ctrl.endpoint.cancel).toHaveBeenCalledWith(
                ctrl.batchId);

            expect(ctrl.stopPolling).toHaveBeenCalled();
            expect(ctrl.closeModal).toHaveBeenCalled();
        });
    });

});
