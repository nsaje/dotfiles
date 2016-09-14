'use strict';
/* eslint-disable camelcase */

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
        var responseData = {
            settings: {
                id: 1,
                name: 'Test Campaign',
                campaign_goal: 3,
                goal_quantity: '0.04',
                target_devices: ['mobile'],
                target_regions: ['NC', '501'],
                campaign_manager: 1,
                iab_category: 'IAB-24',
                enable_ga_tracking: true,
                ga_tracking_type: constants.gaTrackingType.API,
                ga_property_id: 'UA-123-1',
                enable_adobe_tracking: true,
                adobe_tracking_param: 'cid'
            },
            goals: [],
        };
        var requestData = {
            settings: {
                id: 1,
                name: 'Test Campaign',
                campaign_goal: 3,
                goal_quantity: '0.04',
                target_devices: ['mobile'],
                target_regions: ['NC', '501'],
                campaign_manager: 1,
                iab_category: 'IAB-24',
                enable_ga_tracking: true,
                ga_tracking_type: constants.gaTrackingType.API,
                ga_property_id: 'UA-123-1',
                enable_adobe_tracking: true,
                adobe_tracking_param: 'cid'
            },
            goals: {
                primary: null,
                added: [],
                removed: [],
                modified: {},
            },
        };
        var settings = {
            id: 1,
            name: 'Test Campaign',
            campaignGoal: 3,
            goalQuantity: '0.04',
            campaignManager: 1,
            IABCategory: 'IAB-24',
            targetDevices: [{
                name: 'Desktop',
                value: constants.adTargetDevice.DESKTOP,
                checked: false
            }, {
                name: 'Tablet',
                value: constants.adTargetDevice.TABLET,
                checked: false
            }, {
                name: 'Mobile',
                value: constants.adTargetDevice.MOBILE,
                checked: true
            }],
            targetRegions: ['NC', '501'],
            enableGaTracking: true,
            gaTrackingType: constants.gaTrackingType.API,
            gaPropertyId: 'UA-123-1',
            enableAdobeTracking: true,
            adobeTrackingParam: 'cid'
        };

        describe('get', function () {
            it('gets and converts server data', function () {
                var result;
                var data = {data: responseData};

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

                $httpBackend.expectPUT(url, requestData).respond(200, {data: responseData});
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
                        no_goals: ['At least one goal must be defined'],
                        goals: ['CPA goal cannot be set as primary because ...'],
                        goal_quantity: ['Goal quantity is wrong'],
                        target_devices: ['Target devices are wrong'],
                        target_regions: ['Target regions are wrong'],
                        iab_category: ['Invalid IAB category'],
                        campaign_manager: ['Invalid campaign manager'],
                        enable_ga_tracking: ['Invalid campaign manager'],
                        ga_tracking_type: ['Invalid GA tracking type'],
                        ga_property_id: ['Invalid GA property id'],
                        enable_adobe_tracking: ['Invalid adobe tracking'],
                        adobe_tracking_param: ['Invalid adobe tracking param']
                    }
                };

                $httpBackend.expectPUT(url, requestData).respond(400, {data: errorData});
                api.campaignSettings.save(settings).then(null, function (data) {
                    result = data;
                });
                $httpBackend.flush();

                expect(result).toEqual({
                    name: ['Name is wrong'],
                    campaignGoal: ['Campaign goal is wrong'],
                    goalQuantity: ['Goal quantity is wrong'],
                    targetDevices: ['Target devices are wrong'],
                    targetRegions: ['Target regions are wrong'],
                    noGoals: ['At least one goal must be defined'],
                    goals: ['CPA goal cannot be set as primary because ...'],
                    IABCategory: ['Invalid IAB category'],
                    campaignManager: ['Invalid campaign manager'],
                    enableGaTracking: ['Invalid campaign manager'],
                    gaTrackingType: ['Invalid GA tracking type'],
                    gaPropertyId: ['Invalid GA property id'],
                    enableAdobeTracking: ['Invalid adobe tracking'],
                    adobeTrackingParam: ['Invalid adobe tracking param']
                });
            });
        });
    });
});
