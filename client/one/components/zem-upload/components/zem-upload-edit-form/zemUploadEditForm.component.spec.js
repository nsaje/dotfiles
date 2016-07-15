/* globals describe, beforeEach, module, inject, it, expect, constants, angular, spyOn */
'use strict';

describe('ZemUploadEditFormCtrl', function () {
    var scope, api, $q, ctrl, $interval;

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
            save: function () {},
            cancel: function () {},
        };

        ctrl = $controller(
            'ZemUploadEditFormCtrl',
            {$scope: scope},
            {
                api: {},
                endpoint: mockEndpoint,
                callback: function () {},
                batchId: 1,
                scrollTop: function () {}, // directive link function
                scrollBottom: function () {}, // directive link function
            }
        );
    }));

    it('initializes api correctly', function () {
        expect(ctrl.api.open).toBeDefined();
        expect(ctrl.api.close).toBeDefined();
        expect(ctrl.api.update).toBeDefined();
        expect(ctrl.api.selectedId).toBeNull();
        expect(ctrl.api.requestInProgress).toBe(false);
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
            expect(ctrl.selectedCandidate).not.toBe(candidate);
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

            ctrl.api.close();
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
            ctrl.api.open(ctrl.candidates[0]);
            ctrl.batchId = 1234;

            var deferred = $q.defer();
            spyOn(ctrl.endpoint, 'updateCandidate').and.callFake(function () {
                return deferred.promise;
            });

            ctrl.update();
            expect(ctrl.endpoint.updateCandidate).toHaveBeenCalledWith(
                ctrl.selectedCandidate, ctrl.batchId);
            expect(ctrl.api.requestInProgress).toBe(true);
            expect(ctrl.requestFailed).toBe(false);
            expect(ctrl.endpoint.updateCandidate).toHaveBeenCalledWith(
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

            expect(ctrl.api.requestInProgress).toBe(false);
            expect(ctrl.requestFailed).toBe(false);
            expect(ctrl.selectedCandidate).toBeNull();
            expect(ctrl.api.selectedId).toBeNull();
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
            ctrl.api.open(ctrl.candidates[0]);
            ctrl.batchId = 1234;

            var deferred = $q.defer();
            spyOn(ctrl.endpoint, 'updateCandidate').and.callFake(function () {
                return deferred.promise;
            });

            ctrl.api.update();
            expect(ctrl.endpoint.updateCandidate).toHaveBeenCalledWith(
                ctrl.selectedCandidate, ctrl.batchId);
            expect(ctrl.api.requestInProgress).toBe(true);
            expect(ctrl.requestFailed).toBe(false);

            deferred.reject({});
            scope.$digest();

            expect(ctrl.api.requestInProgress).toBe(false);
            expect(ctrl.requestFailed).toBe(true);
            expect(ctrl.selectedCandidate).not.toBeNull();
        });
    });
});
