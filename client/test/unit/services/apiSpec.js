'use strict';

describe('api', function() {
    var $httpBackend, api;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(inject(function(_$httpBackend_, _api_) {
        $httpBackend = _$httpBackend_;
        api = _api_;
    }));

    afterEach(function() {
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    describe('adGroupAdsPlusUpload', function() {
        var adGroupId = 123;
        var url = '/api/ad_groups/' + adGroupId + '/contentads_plus/upload/';

        describe('getDefaults', function() {
            it('get settings defaults', function() {
                var result;
                var data = {
                    data: {
                        defaults: {
                            display_url: 'test.com',
                            brand_name: 'brand',
                            description: 'description',
                            call_to_action: 'call'
                        }
                    }
                };

                $httpBackend.expectGET(url).respond(200, data);
                api.adGroupAdsPlusUpload.getDefaults(adGroupId).then(function(data) {
                    result = data;
                });
                $httpBackend.flush();

                expect(result.defaults).toEqual({
                    displayUrl: 'test.com',
                    brandName: 'brand',
                    description: 'description',
                    callToAction: 'call'
                });
            });
        });

        describe('upload', function() {
            var file = new Blob([], {type: 'text/csv'});
            var batchName = 'testname';

            it('uploads given file to a correct url', function() {
                var resolvedData;

                $httpBackend.expectPOST(url).respond(200, {data: {batch_id: 123}});

                api.adGroupAdsPlusUpload.upload(adGroupId, file, batchName).then(function(data) {
                    resolvedData = data;
                });
                $httpBackend.flush();

                expect(resolvedData).toBe(123);
            });

            it('returns converted validation errors on failure', function() {
                var result;
                var data = {
                    data: {
                        errors: {
                            batch_name: 'Batch name error message.',
                            content_ads: 'Error message.',
                            display_url: 'test.com',
                            brand_name: 'brand',
                            description: 'description',
                            call_to_action: 'call'
                        }
                    }
                };

                $httpBackend.expectPOST(url).respond(400, data);
                api.adGroupAdsPlusUpload.upload(adGroupId, file, batchName).then(null, function(errors) {
                    result = errors;
                });
                $httpBackend.flush();

                expect(result).toEqual({
                    errors: {
                        file: 'Error message.',
                        batchName: 'Batch name error message.',
                        displayUrl: 'test.com',
                        brandName: 'brand',
                        description: 'description',
                        callToAction: 'call'
                    }
                });
            });
        });
    });
});
