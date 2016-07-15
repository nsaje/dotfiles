/* globals describe, beforeEach, module, inject, it, expect, constants, angular, spyOn */
'use strict';

describe('ZemUploadStep2Ctrl', function () {
    var scope, api, $q, ctrl, $interval;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(inject(function ($controller, $rootScope, _$q_, _$interval_) {
        $q = _$q_;
        $interval = _$interval_;
        scope = $rootScope.$new();
        var mockApi = {
            upload: function () {},
            checkStatus: function () {},
            updateCandidate: function () {},
            removeCandidate: function () {},
            save: function () {},
            cancel: function () {},
        };

        ctrl = $controller(
            'ZemUploadStep2Ctrl',
            {$scope: scope},
            {
                api: mockApi,
                callback: function () {},
                candidates: [],
                batchId: 1,
                batchName: 'mock batch',
                onSave: function () {},
                closeModal: function () {},
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
            }];
        });

        it('updates candidates on success', function () {
            ctrl.candidates = angular.copy(candidates);

            var deferred = $q.defer();
            spyOn(ctrl.api, 'checkStatus').and.callFake(function () {
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

        it('does nothing on failure', function () {
            ctrl.candidates = angular.copy(candidates);

            var deferred = $q.defer();
            spyOn(ctrl.api, 'checkStatus').and.callFake(function () {
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
            spyOn(ctrl.api, 'checkStatus').and.callFake(function () {
                return deferred.promise;
            });
            ctrl.startPolling();
            $interval.flush(2501);

            expect(ctrl.api.checkStatus).toHaveBeenCalledWith(ctrl.batchId, [1]);
        });

        it('stops polling when no candidates are left waiting', function () {
            ctrl.candidates = angular.copy(candidates);

            var deferred = $q.defer();
            spyOn(ctrl.api, 'checkStatus').and.callFake(function () {
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

    describe('edit form open', function () {
        var candidate;
        beforeEach(function () {
            candidate = {
                url: 'http://zemanta.com',
                title: 'Zemanta Blog',
                imageUrl: 'http://zemanta.com/img.jpg',
                imageCrop: 'center',
                description: '',
                displayUrl: 'zemanta.com',
                brandName: 'Zemanta',
                callToAction: 'Read more',
                label: 'blog',
                errors: {
                    imageUrl: ['Invalid image URL'],
                    description: ['Missing description'],
                },
            };
        });

        it('initializes edit form properties', function () {
            ctrl.openEditForm(candidate);
            expect(ctrl.selectedCandidate).not.toBe(candidate);
            expect(ctrl.selectedCandidate.defaults).toEqual({});
            expect(ctrl.selectedCandidate.useTrackers).toBe(false);
            expect(ctrl.selectedCandidate.useSecondaryTracker).toBe(false);
        });

        it('sets tracker url booleans', function () {
            candidate.primaryTrackerUrl = 'https://zemanta.com/px1';
            candidate.secondaryTrackerUrl = 'https://zemanta.com/px2';

            ctrl.openEditForm(candidate);
            expect(ctrl.selectedCandidate.useTrackers).toBe(true);
            expect(ctrl.selectedCandidate.useSecondaryTracker).toBe(true);
        });
    });

    describe('edit form close', function () {
        it('removes edit form properties', function () {
            ctrl.selectedCandidate = {
                url: 'http://zemanta.com',
                title: 'Zemanta Blog',
                imageUrl: 'http://zemanta.com/img.jpg',
                imageCrop: 'center',
                description: '',
                displayUrl: 'zemanta.com',
                brandName: 'Zemanta',
                callToAction: 'Read more',
                label: 'blog',
                primaryTrackerUrl: 'https://zemanta.com/px1',
                secondaryTrackerUrl: 'https://zemanta.com/px2',
                errors: {
                    imageUrl: ['Invalid image URL'],
                    description: ['Missing description'],
                },
                defaults: {
                    description: true,
                    displayUrl: true,
                },
                useTrackers: true,
                useSecondaryTracker: false,
            };

            ctrl.closeEditForm();
            expect(ctrl.selectedCandidate).toBeNull();
        });
    });

    describe('candidate update', function () {
        it('closes edit form and updates candidates on success', function () {
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
            ctrl.openEditForm(ctrl.candidates[0]);
            ctrl.batchId = 1234;

            var deferred = $q.defer();
            spyOn(ctrl.api, 'updateCandidate').and.callFake(function () {
                return deferred.promise;
            });

            spyOn(ctrl, 'startPolling').and.stub();

            ctrl.updateCandidate();
            expect(ctrl.api.updateCandidate).toHaveBeenCalledWith(
                ctrl.selectedCandidate, ctrl.batchId);
            expect(ctrl.updateRequestInProgress).toBe(true);
            expect(ctrl.updateRequestFailed).toBe(false);
            expect(ctrl.api.updateCandidate).toHaveBeenCalledWith(
                ctrl.selectedCandidate, ctrl.batchId);

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
                candidates: [returnedCandidate],
            });
            scope.$digest();

            expect(ctrl.updateRequestInProgress).toBe(false);
            expect(ctrl.updateRequestFailed).toBe(false);
            expect(ctrl.startPolling).toHaveBeenCalled();
            expect(ctrl.selectedCandidate).toBeNull();
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
            ctrl.openEditForm(ctrl.candidates[0]);
            ctrl.batchId = 1234;

            var deferred = $q.defer();
            spyOn(ctrl.api, 'updateCandidate').and.callFake(function () {
                return deferred.promise;
            });

            spyOn(ctrl, 'startPolling').and.stub();

            ctrl.updateCandidate();
            expect(ctrl.api.updateCandidate).toHaveBeenCalledWith(
                ctrl.selectedCandidate, ctrl.batchId);
            expect(ctrl.updateRequestInProgress).toBe(true);
            expect(ctrl.updateRequestFailed).toBe(false);

            deferred.reject({});
            scope.$digest();

            expect(ctrl.updateRequestInProgress).toBe(false);
            expect(ctrl.updateRequestFailed).toBe(true);
            expect(ctrl.startPolling).not.toHaveBeenCalled();
            expect(ctrl.selectedCandidate).not.toBeNull();
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
            ctrl.openEditForm(ctrl.candidates[0]);
            ctrl.batchId = 1234;

            var deferred = $q.defer();
            spyOn(ctrl.api, 'removeCandidate').and.callFake(function () {
                return deferred.promise;
            });

            var mockEvent = {
                stopPropagation: function () {},
            };
            spyOn(mockEvent, 'stopPropagation');
            ctrl.removeCandidate(candidate, mockEvent);
            expect(mockEvent.stopPropagation).toHaveBeenCalled();
            expect(ctrl.api.removeCandidate).toHaveBeenCalledWith(
                candidate.id, ctrl.batchId);
            expect(candidate.removeRequestInProgress).toBe(true);
            expect(candidate.removeRequestFailed).toBe(false);

            deferred.resolve();
            scope.$digest();

            expect(ctrl.selectedCandidate).toBeNull();
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
            ctrl.openEditForm(ctrl.candidates[0]);
            ctrl.batchId = 1234;

            var deferred = $q.defer();
            spyOn(ctrl.api, 'removeCandidate').and.callFake(function () {
                return deferred.promise;
            });

            var mockEvent = {
                stopPropagation: function () {},
            };
            spyOn(mockEvent, 'stopPropagation');
            ctrl.removeCandidate(candidate, mockEvent);
            expect(mockEvent.stopPropagation).toHaveBeenCalled();
            expect(ctrl.api.removeCandidate).toHaveBeenCalledWith(
                candidate.id, ctrl.batchId);
            expect(candidate.removeRequestInProgress).toBe(true);
            expect(candidate.removeRequestFailed).toBe(false);

            deferred.reject();
            scope.$digest();

            expect(candidate.removeRequestInProgress).toBe(false);
            expect(candidate.removeRequestFailed).toBe(true);
            expect(ctrl.selectedCandidate).not.toBeNull();
            expect(ctrl.candidates.length).toEqual(1);
        });
    });

    describe('upload save', function () {
        it('switches to last step on success', function () {
            var deferred = $q.defer();
            spyOn(ctrl.api, 'save').and.callFake(function () {
                return deferred.promise;
            });
            spyOn(ctrl, 'callback').and.stub();

            ctrl.batchId = 1234;
            ctrl.formData.batchName = 'new batch name';

            ctrl.save();
            expect(ctrl.api.save).toHaveBeenCalledWith(
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
            spyOn(ctrl.api, 'save').and.callFake(function () {
                return deferred.promise;
            });
            spyOn(ctrl, 'callback').and.stub();

            ctrl.batchId = 1234;
            ctrl.formData.batchName = 'new batch name';

            ctrl.save();
            expect(ctrl.api.save).toHaveBeenCalledWith(
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
            spyOn(ctrl.api, 'cancel').and.callFake(function () {
                return deferred.promise;
            });
            spyOn(ctrl, 'stopPolling').and.stub();
            spyOn(ctrl, 'closeModal');

            ctrl.batchId = 1234;

            ctrl.cancel();
            expect(ctrl.api.cancel).toHaveBeenCalledWith(
                ctrl.batchId);

            expect(ctrl.stopPolling).toHaveBeenCalled();
            expect(ctrl.closeModal).toHaveBeenCalled();
        });
    });

});
