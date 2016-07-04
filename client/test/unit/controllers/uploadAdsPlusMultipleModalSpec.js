/* globals describe, beforeEach, module, inject, it, expect, constants, angular, spyOn, jasmine */
'use strict';

describe('UploadAdsPlusMultipleModalCtrl', function () {
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
                uploadMultiple: function () {},
                checkStatus: function () {},
                updateCandidate: function () {},
                removeCandidate: function () {},
                save: function () {},
                cancel: function () {},
            },
        };

        $state = _$state_;
        $state.params = {id: 123};

        var mockedDate = new Date(Date.UTC(2016, 6, 1, 15, 5));
        jasmine.clock().mockDate(mockedDate);

        $controller(
            'UploadAdsPlusMultipleModalCtrl',
            {$scope: $scope, $modalInstance: $modalInstance, api: api, $state: $state, errors: {}}
        );
    }));

    describe('upload', function () {
        it('switches to picker on success', function () {
            var deferred = $q.defer();
            spyOn(api.uploadPlus, 'uploadMultiple').and.callFake(function () {
                return deferred.promise;
            });

            $scope.uploadFormData = {
                file: 'testfile',
                batchName: 'testname',
            };
            $scope.uploadFormData.file = 'testfile';
            spyOn($scope, 'startPolling').and.stub();
            spyOn($scope, 'switchToContentAdPicker').and.stub();

            $scope.upload();
            expect(api.uploadPlus.uploadMultiple).toHaveBeenCalledWith(
                $state.params.id, {file: $scope.uploadFormData.file, batchName: $scope.uploadFormData.batchName}
            );

            var candidates = [{
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
            var batchId = 1234;
            deferred.resolve({
                candidates: candidates,
                batchId: batchId,
            });
            $scope.$root.$digest();

            expect($scope.candidates).toEqual(candidates);
            expect($scope.batchId).toEqual(batchId);
            expect($scope.switchToContentAdPicker).toHaveBeenCalled();
            expect($scope.startPolling).toHaveBeenCalled();
        });

        it('uses current datetime as default batch name', function () {
            expect($scope.uploadFormData.batchName).toEqual('7/1/2016 3:05 PM');
        });

        it('displays errors on failure', function () {
            var deferred = $q.defer();
            spyOn(api.uploadPlus, 'uploadMultiple').and.callFake(function () {
                return deferred.promise;
            });

            $scope.uploadFormData = {
                file: 'testfile',
                batchName: 'testname',
            };
            spyOn($scope, 'startPolling').and.stub();
            spyOn($scope, 'switchToContentAdPicker').and.stub();

            $scope.upload();
            expect(api.uploadPlus.uploadMultiple).toHaveBeenCalledWith(
                $state.params.id, {file: $scope.uploadFormData.file, batchName: $scope.uploadFormData.batchName}
            );

            var errors = {
                batchName: ['Missing batch name'],
                file: ['Missing file'],
            };
            deferred.reject({
                errors: errors,
            });
            $scope.$root.$digest();

            expect($scope.uploadFormErrors).toEqual(errors);
            expect($scope.switchToContentAdPicker).not.toHaveBeenCalled();
            expect($scope.startPolling).not.toHaveBeenCalled();
        });
    });

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
            $scope.candidates = angular.copy(candidates);

            var deferred = $q.defer();
            spyOn(api.uploadPlus, 'checkStatus').and.callFake(function () {
                return deferred.promise;
            });
            $scope.startPolling();
            $interval.flush(2501);

            deferred.reject();
            $scope.$root.$digest();

            expect($scope.candidates).toEqual(candidates);
            $interval.flush(2500);
            $scope.$root.$digest();

            expect($scope.pollInterval).not.toBeNull();
        });

        it('does nothing on failure', function () {
            $scope.candidates = angular.copy(candidates);

            var deferred = $q.defer();
            spyOn(api.uploadPlus, 'checkStatus').and.callFake(function () {
                return deferred.promise;
            });
            spyOn($interval, 'cancel');
            $scope.startPolling();
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

            $scope.$root.$digest();
            expect($scope.candidates).toEqual([resolvedCandidate]);
            expect($interval.cancel).not.toHaveBeenCalled();

            $interval.flush(2500);
            expect($interval.cancel).toHaveBeenCalled();
            expect($scope.pollInterval).toBeNull();
        });

        it('polls only for candidates that are waiting', function () {
            $scope.candidates = angular.copy(candidates);
            $scope.candidates.push({
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
            $scope.batchId = 1234;

            var deferred = $q.defer();
            spyOn(api.uploadPlus, 'checkStatus').and.callFake(function () {
                return deferred.promise;
            });
            $scope.startPolling();
            $interval.flush(2501);

            expect(api.uploadPlus.checkStatus).toHaveBeenCalledWith($state.params.id, $scope.batchId, [1]);
        });

        it('stops polling when no candidates are left waiting', function () {
            $scope.candidates = angular.copy(candidates);

            var deferred = $q.defer();
            spyOn(api.uploadPlus, 'checkStatus').and.callFake(function () {
                return deferred.promise;
            });
            spyOn($interval, 'cancel');
            $scope.startPolling();
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

            $scope.$root.$digest();
            expect($scope.candidates).toEqual([resolvedCandidate]);
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
            $scope.openEditForm(candidate);
            expect($scope.selectedCandidate).not.toBe(candidate);
            expect($scope.selectedCandidate.defaults).toEqual({});
            expect($scope.selectedCandidate.useTrackers).toBe(false);
            expect($scope.selectedCandidate.useSecondaryTracker).toBe(false);
        });

        it('sets tracker url booleans', function () {
            candidate.primaryTrackerUrl = 'https://zemanta.com/px1';
            candidate.secondaryTrackerUrl = 'https://zemanta.com/px2';

            $scope.openEditForm(candidate);
            expect($scope.selectedCandidate.useTrackers).toBe(true);
            expect($scope.selectedCandidate.useSecondaryTracker).toBe(true);
        });
    });

    describe('edit form close', function () {
        it('removes edit form properties', function () {
            $scope.selectedCandidate = {
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

            $scope.closeEditForm();
            expect($scope.selectedCandidate).toBeNull();
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
            $scope.candidates = [candidate];
            $scope.openEditForm($scope.candidates[0]);
            $scope.batchId = 1234;

            var deferred = $q.defer();
            spyOn(api.uploadPlus, 'updateCandidate').and.callFake(function () {
                return deferred.promise;
            });

            spyOn($scope, 'startPolling').and.stub();

            $scope.updateCandidate();
            expect(api.uploadPlus.updateCandidate).toHaveBeenCalledWith(
                $scope.selectedCandidate, $state.params.id, $scope.batchId);

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
            $scope.$root.$digest();

            expect($scope.startPolling).toHaveBeenCalled();
            expect($scope.selectedCandidate).toBeNull();
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
            $scope.candidates = [candidate];
            $scope.openEditForm($scope.candidates[0]);
            $scope.batchId = 1234;

            var deferred = $q.defer();
            spyOn(api.uploadPlus, 'removeCandidate').and.callFake(function () {
                return deferred.promise;
            });

            var mockEvent = {
                stopPropagation: function () {},
            };
            spyOn(mockEvent, 'stopPropagation');
            $scope.removeCandidate(candidate, mockEvent);
            expect(mockEvent.stopPropagation).toHaveBeenCalled();
            expect(api.uploadPlus.removeCandidate).toHaveBeenCalledWith(
                candidate.id, $state.params.id, $scope.batchId);

            deferred.resolve();
            $scope.$root.$digest();

            expect($scope.selectedCandidate).toBeNull();
            expect($scope.candidates).toEqual([]);
        });
    });

    describe('upload save', function () {
        it('switches to last step on success', function () {
            var deferred = $q.defer();
            spyOn(api.uploadPlus, 'save').and.callFake(function () {
                return deferred.promise;
            });
            spyOn($scope, 'switchToSuccessScreen').and.stub();

            $scope.batchId = 1234;
            $scope.uploadFormData.batchName = 'new batch name';

            $scope.save();
            expect(api.uploadPlus.save).toHaveBeenCalledWith(
                $state.params.id, $scope.batchId, $scope.uploadFormData.batchName);

            var numSuccessful = 50;
            deferred.resolve({
                numSuccessful: numSuccessful,
            });
            $scope.$root.$digest();

            expect($scope.switchToSuccessScreen).toHaveBeenCalled();
            expect($scope.numSuccessful).toEqual(numSuccessful);
        });
    });

    describe('upload cancel', function () {
        it('closes the modal window', function () {
            var deferred = $q.defer();
            spyOn(api.uploadPlus, 'cancel').and.callFake(function () {
                return deferred.promise;
            });
            spyOn($scope, 'stopPolling').and.stub();
            spyOn($modalInstance, 'close');

            $scope.batchId = 1234;

            $scope.cancel();
            expect(api.uploadPlus.cancel).toHaveBeenCalledWith(
                $state.params.id, $scope.batchId);

            expect($scope.stopPolling).toHaveBeenCalled();
            expect($modalInstance.close).toHaveBeenCalled();
        });
    });

    describe('upload reset', function () {
        it('resets controller variables', function () {
            $scope.candidates = [{
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
            $scope.selectedCandidate = $scope.candidates[0];
            $scope.step = 3;
            $scope.batchId = 1234;
            $scope.batchNameEdit = true;
            $scope.uploadFormData = {
                batchName: 'test batch name',
                file: 'test file',
            };
            $scope.anyCandidateHasErrors = true;
            $scope.numSuccessful = 123;
            $scope.saveErrors = {
                batchName: ['Invalid batch name'],
            };
            $scope.uploadFormErrors = {
                batchName: ['Invalid batch name'],
            };

            spyOn($scope, 'stopPolling').and.stub();

            $scope.switchToFileUpload();
            expect($scope.step).toEqual(1);
            expect($scope.candidates).toEqual([]);
            expect($scope.selectedCandidate).toBeNull();
            expect($scope.batchNameEdit).toBe(false);
            expect($scope.uploadFormData).toEqual({
                batchName: '7/1/2016 3:05 PM',
            });
            expect($scope.anyCandidateHasErrors).toBe(false);
            expect($scope.batchId).toBeNull();
            expect($scope.numSuccessful).toBeNull();
            expect($scope.saveErrors).toBeNull();
            expect($scope.uploadFormErrors).toBeNull();
            expect($scope.stopPolling).toHaveBeenCalled();
        });
    });
});
