/* globals describe, beforeEach, module, inject, it, expect, constants, angular, spyOn */
'use strict';

describe('ZemUploadEditFormCtrl', function () {
    var scope, api, $q, ctrl, $interval, $timeout;

    beforeEach(module('one'));
    beforeEach(module('one.mocks.zemInitializationService'));
    beforeEach(module('stateMock'));

    beforeEach(inject(function ($controller, $rootScope, _$q_, _$interval_, _$timeout_) {
        $q = _$q_;
        $interval = _$interval_;
        $timeout = _$timeout_;
        scope = $rootScope.$new();
        var mockEndpoint = {
            upload: function () {},
            checkStatus: function () {},
            updateCandidate: function () {},
            removeCandidate: function () {},
            getCandidates: function () {},
            save: function () {},
            cancel: function () {},
        };

        ctrl = $controller(
            'ZemUploadEditFormCtrl',
            {$scope: scope},
            {
                api: {},
                endpoint: mockEndpoint,
                refreshCallback: function () {},
                updateCallback: function () {},
                batchId: 1,
                scrollTop: function () {}, // directive link function
            }
        );
    }));

    beforeEach(inject(function ($httpBackend) {
        // when using $timeout.flush these api endpoints get called
        $httpBackend.when('GET', '/api/users/current/').respond({});
        $httpBackend.when('GET', '/api/all_accounts/nav/').respond({});
    }));

    it('initializes api correctly', function () {
        expect(ctrl.api.open).toBeDefined();
        expect(ctrl.api.close).toBeDefined();
        expect(ctrl.api.selectedId).toBeNull();
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
            ctrl.api.open(candidate);
            expect(ctrl.selectedCandidate).toBe(candidate);
            expect(ctrl.selectedCandidate.defaults).toEqual({});
            expect(ctrl.selectedCandidate.useTrackers).toBe(false);
            expect(ctrl.selectedCandidate.useSecondaryTracker).toBe(false);
            expect(ctrl.api.selectedId).toBe(ctrl.selectedCandidate.id);
        });

        it('sets tracker url booleans', function () {
            candidate.primaryTrackerUrl = 'https://zemanta.com/px1';
            candidate.secondaryTrackerUrl = 'https://zemanta.com/px2';

            ctrl.api.open(candidate);
            expect(ctrl.selectedCandidate.useTrackers).toBe(true);
            expect(ctrl.selectedCandidate.useSecondaryTracker).toBe(true);
        });
    });

    describe('edit form close', function () {
        it('refreshes candidates list and removes edit form properties', function () {
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

            spyOn(ctrl, 'refreshCallback').and.stub();
            var deferred = $q.defer();
            spyOn(ctrl.endpoint, 'getCandidates').and.callFake(function () {
                return deferred.promise;
            });

            ctrl.api.close();
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

            expect(ctrl.selectedCandidate).toBeNull();
            expect(ctrl.api.selectedId).toBeNull();
            expect(ctrl.refreshCallback).toHaveBeenCalled();
        });
    });

    describe('update field', function () {
        it('calls the endpoint', function () {
            ctrl.batchId = 1234;
            ctrl.selectedCandidate = {
                id: 1,
                title: 'ad title',
                url: 'http://example.com',
                errors: {},
            };

            var deferred = $q.defer();
            spyOn(ctrl.endpoint, 'updateCandidate').and.callFake(function () {
                return deferred.promise;
            });
            ctrl.updateField('title');
            expect(ctrl.fieldsLoading.title).toBe(true);
            expect(ctrl.fieldsSaved.title).toBe(false);

            deferred.resolve({
                updatedFields: {
                    title: 'ad title',
                },
                errors: {},
            });
            scope.$digest();

            expect(ctrl.fieldsLoading.title).toBe(false);
            expect(ctrl.fieldsSaved.title).toBe(true);
            expect(ctrl.endpoint.updateCandidate).toHaveBeenCalledWith(1234, {
                id: 1,
                title: 'ad title',
            }, []);
        });

        it('adds defaults', function () {
            ctrl.batchId = 1234;
            ctrl.selectedCandidate = {
                id: 1,
                description: 'description',
                errors: {},
            };

            spyOn(ctrl, 'updateCallback').and.stub();

            var deferred = $q.defer();
            spyOn(ctrl.endpoint, 'updateCandidate').and.callFake(function () {
                return deferred.promise;
            });
            ctrl.updateField('description', true);
            expect(ctrl.fieldsLoading.description).toBe(true);
            expect(ctrl.fieldsSaved.description).toBe(false);

            deferred.resolve({
                updatedFields: {
                    description: 'description',
                },
                errors: {},
            });
            scope.$digest();

            expect(ctrl.fieldsLoading.description).toBe(false);
            expect(ctrl.fieldsSaved.description).toBe(true);
            expect(ctrl.endpoint.updateCandidate).toHaveBeenCalledWith(1234, {
                id: 1,
                description: 'description',
            }, ['description']);
            expect(ctrl.updateCallback).toHaveBeenCalledWith(['description']);
        });

        it('retries on fail', function () {
            ctrl.batchId = 1234;
            ctrl.selectedCandidate = {
                id: 1,
                title: 'ad title',
                url: 'http://example.com',
                errors: {},
            };

            var firstDeferred = $q.defer(),
                secondDeferred = $q.defer();
            var firstCall = true;
            spyOn(ctrl.endpoint, 'updateCandidate').and.returnValues(firstDeferred.promise, secondDeferred.promise);
            ctrl.updateField('title');

            firstDeferred.reject({});
            secondDeferred.resolve({
                updatedFields: {
                    title: 'ad title',
                },
                errors: {},
            });
            scope.$digest();

            $timeout.flush(10000);
            scope.$digest();

            expect(ctrl.endpoint.updateCandidate).toHaveBeenCalledWith(1234, {
                id: 1,
                title: 'ad title',
            }, []);
        });

        it('saves returned errors', function () {
            ctrl.batchId = 1234;
            ctrl.selectedCandidate = {
                id: 1,
                title: 'ad title',
                url: 'http://example.com',
                errors: {},
            };

            spyOn(ctrl, 'updateCallback').and.stub();

            var updateDeferred = $q.defer();
            spyOn(ctrl.endpoint, 'updateCandidate').and.callFake(function () {
                return updateDeferred.promise;
            });

            var statusDeferred = $q.defer();
            spyOn(ctrl.endpoint, 'getCandidates').and.callFake(function () {
                return statusDeferred.promise;
            });

            ctrl.updateField('title');
            expect(ctrl.fieldsLoading.title).toBe(true);
            expect(ctrl.fieldsSaved.title).toBe(false);

            updateDeferred.resolve({
                updatedFields: {},
                errors: {
                    title: ['Invalid title'],
                },
            });
            statusDeferred.resolve({
                candidates: [{
                    id: 1,
                    title: 'ad title',
                    url: 'http://example.com',
                    errors: {},
                }]
            });

            scope.$digest();

            expect(ctrl.fieldsLoading.title).toBe(false);
            expect(ctrl.fieldsSaved.title).toBe(true);
            expect(ctrl.endpoint.updateCandidate).toHaveBeenCalledWith(1234, {
                id: 1,
                title: 'ad title',
            }, []);
            expect(ctrl.selectedCandidate.errors).toEqual({
                title: ['Invalid title'],
            });
            expect(ctrl.updateCallback).toHaveBeenCalled();
        });
    });
});
