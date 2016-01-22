'use strict';

describe('api', function () {
    var $httpBackend, api;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(inject(function (_$httpBackend_, _api_) {
        $httpBackend = _$httpBackend_;
        api = _api_;
    }));

    afterEach(function () {
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    describe('demo', function () {
        function objForEach (obj, fun) {
            for (var key in obj) {
                if (obj.hasOwnProperty(key)) {
                    fun.call(obj, obj[key], key);
                }
            }
        }
        function getFunName (fun) {
            var name = /^function\s+([\w\$]+)\s*\(/.exec(fun.toString());
            return name ? name[1] : null;
        }
        it('does not mock api methods if demo is inactive', function () {
            objForEach(api, function (obj, objName) {
                objForEach(obj, function (fun, funName) {
                    expect(getFunName(fun)).not.toBe('demo');
                });
            });
        });
    });

    describe('CampaignSettings', function () {
        var campaignId = 1;
        var url = '/api/campaigns/' + campaignId + '/settings/';
        var serverData = {
            settings: {
                id: 1,
                name: 'Test Campaign',
                campaign_goal: 3,
                goal_quantity: '0.04',
                target_devices: ['mobile'],
                target_regions: ['NC', '501']
            }
        };
        var settings = {
            id: 1,
            name: 'Test Campaign',
            campaignGoal: 3,
            goalQuantity: '0.04',
            targetDevices: [{
                name: 'Desktop',
                value: constants.adTargetDevice.DESKTOP,
                checked: false
            }, {
                name: 'Mobile',
                value: constants.adTargetDevice.MOBILE,
                checked: true
            }],
            targetRegions: ['NC', '501']
        };

        describe('get', function () {
            it('gets and converts server data', function () {
                var result;
                var data = {data: serverData};

                $httpBackend.expectGET(url).respond(200, data);
                api.campaignSettings.get(campaignId).then(function (data) {
                    result = data;
                });
                $httpBackend.flush();

                expect(result.settings).toEqual(settings);
            });
        });

        describe('save', function () {
            it('converts and saves data', function () {
                var result;

                $httpBackend.expectPUT(url, serverData).respond(200, {data: serverData});
                api.campaignSettings.save(settings).then(function (data) {
                    result = data;
                });
                $httpBackend.flush();

                expect(result.settings).toEqual(settings);
            });

            it('converts validation errors in case of failure', function () {
                var result;
                var errorData = {
                    error_code: 'ValidationError',
                    errors: {
                        name: ['Name is wrong'],
                        campaign_goal: ['Campaign goal is wrong'],
                        goal_quantity: ['Goal quantity is wrong'],
                        target_devices: ['Target devices are wrong'],
                        target_regions: ['Target regions are wrong']
                    }
                };

                $httpBackend.expectPUT(url, serverData).respond(400, {data: errorData});
                api.campaignSettings.save(settings).then(null, function (data) {
                    result = data;
                });
                $httpBackend.flush();

                expect(result).toEqual({
                    name: ['Name is wrong'],
                    campaignGoal: ['Campaign goal is wrong'],
                    goalQuantity: ['Goal quantity is wrong'],
                    targetDevices: ['Target devices are wrong'],
                    targetRegions: ['Target regions are wrong']
                });
            });
        });
    });

    describe('adGroupAdsPlusUpload', function () {
        var adGroupId = 123;
        var url = '/api/ad_groups/' + adGroupId + '/contentads_plus/upload/';

        describe('getDefaults', function () {
            it('get settings defaults', function () {
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
                api.adGroupAdsPlusUpload.getDefaults(adGroupId).then(function (data) {
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

        describe('upload', function () {
            var file = new Blob([], {type: 'text/csv'});
            var batchName = 'testname';

            it('uploads given file to a correct url', function () {
                var resolvedData;

                $httpBackend.expectPOST(url).respond(200, {data: {batch_id: 123}});

                api.adGroupAdsPlusUpload.upload(adGroupId, file, batchName).then(function (data) {
                    resolvedData = data;
                });
                $httpBackend.flush();

                expect(resolvedData).toBe(123);
            });

            it('returns converted validation errors on failure', function () {
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
                api.adGroupAdsPlusUpload.upload(adGroupId, file, batchName).then(null, function (errors) {
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
