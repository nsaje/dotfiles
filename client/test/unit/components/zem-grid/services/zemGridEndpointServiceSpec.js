/* globals angular, constants, moment, jasmine, describe, it, beforeEach, expect, module, inject, spyOn */

describe('zemGridEndpointServiceSpec', function () {
    var $scope;
    var $q;
    var $httpBackend;
    var zemGridEndpointService;
    var zemGridEndpointApiConverter;
    var zemGridEndpointColumns;
    var zemGridEndpointApi;

    beforeEach(module('one'));

    beforeEach(inject(function (_$httpBackend_) {
        $httpBackend = _$httpBackend_;
        $httpBackend.when('GET', '/api/users/current/').respond({data: {user: {id: 1, permissions: {}}}});
        $httpBackend.when('GET', '/api/all_accounts/nav/').respond({data: {}});
    }));

    beforeEach(inject(function ($rootScope, _$q_, _zemGridEndpointService_, _zemGridEndpointColumns_, _zemGridEndpointApi_, _zemGridEndpointApiConverter_) { // eslint-disable-line max-len
        $q = _$q_;
        zemGridEndpointService = _zemGridEndpointService_;
        zemGridEndpointColumns = _zemGridEndpointColumns_;
        zemGridEndpointApi = _zemGridEndpointApi_;
        zemGridEndpointApiConverter = _zemGridEndpointApiConverter_;

        $scope = $rootScope.$new();
        $scope.isPermissionInternal = function () {
            return false;
        };
        $scope.hasPermission = function () {
            return true;
        };
    }));

    it('should be able to create metadata for all level/breakdown variations', function () {
        var anyMetaData = {
            id: jasmine.any(Number),
            level: jasmine.any(String),
            breakdown: jasmine.any(String),
            columns: jasmine.any(Array),
            categories: jasmine.any(Array),
            breakdownGroups: jasmine.any(Array),
            localStoragePrefix: jasmine.any(String),
            ext: jasmine.any(Object),
        };

        var variations = [
            {level: constants.level.ALL_ACCOUNTS, breakdown: constants.breakdown.ACCOUNT},
            {level: constants.level.ALL_ACCOUNTS, breakdown: constants.breakdown.MEDIA_SOURCE},
            {level: constants.level.ACCOUNTS, breakdown: constants.breakdown.CAMPAIGN},
            {level: constants.level.ACCOUNTS, breakdown: constants.breakdown.MEDIA_SOURCE},
            {level: constants.level.CAMPAIGNS, breakdown: constants.breakdown.AD_GROUP},
            {level: constants.level.CAMPAIGNS, breakdown: constants.breakdown.MEDIA_SOURCE},
            {level: constants.level.AD_GROUPS, breakdown: constants.breakdown.CONTENT_AD},
            {level: constants.level.AD_GROUPS, breakdown: constants.breakdown.MEDIA_SOURCE},
            {level: constants.level.AD_GROUPS, breakdown: constants.breakdown.PUBLISHER},
        ];

        variations.forEach(function (variation) {
            var metaData = zemGridEndpointService.createMetaData($scope, variation.level, 1, variation.breakdown);
            expect(metaData).toEqual(anyMetaData);
        });
    });

    it('should return metadata passed in initialization', function () {
        var metaData = zemGridEndpointService.createMetaData($scope, constants.level.ACCOUNTS, 1, constants.breakdown.CAMPAIGN);
        var endpoint = zemGridEndpointService.createEndpoint(metaData);

        var promise = endpoint.getMetaData();
        $scope.$apply();
        expect(promise.$$state.value).toBe(metaData);
    });

    it('should convert fetched data and update goal columns', function () {
        var metaData = zemGridEndpointService.createMetaData($scope, constants.level.ACCOUNTS, 1, constants.breakdown.CAMPAIGN);
        var endpoint = zemGridEndpointService.createEndpoint(metaData);

        var breakdown = {
            breakdown_id: 1,
            rows: [{}, {}],
            totals: [],
            pagination: {
                offset: 0,
                limit: 2,
                count: 2,
            }
        };

        var config = {
            level: 1,
            limit: 3,
            startDate: moment(),
            endDate: moment(),
            breakdown: [metaData.breakdownGroups[0].breakdowns[0]],
        };

        $httpBackend.when('POST', '/api/accounts/1/breakdown/campaign/').respond({data: [breakdown]});
        spyOn(zemGridEndpointApiConverter, 'convertBreakdownFromApi').and.callThrough();
        spyOn(zemGridEndpointColumns, 'updateConversionGoalColumns');
        spyOn(zemGridEndpointColumns, 'updateOptimizationGoalColumns');

        endpoint.getData(config);
        $httpBackend.flush();
        $scope.$apply();

        expect(zemGridEndpointApiConverter.convertBreakdownFromApi).toHaveBeenCalled();
        expect(zemGridEndpointColumns.updateConversionGoalColumns).toHaveBeenCalled();
        expect(zemGridEndpointColumns.updateOptimizationGoalColumns).toHaveBeenCalled();
    });

    it('should save data using endpoint api', function () {
        var value = 1;
        var column = {field: 'field'};
        var row = {
            breakdownId: 'breakdown',
            stats: {
                field: {
                    property: 'some property',
                    value: {
                        valueProperty: 0
                    },
                },
            }
        };
        var api = {
            save: jasmine.createSpy().and.returnValue(
                $q.resolve({
                    field: {valueProperty: value}
                })
            ),
        };
        spyOn(zemGridEndpointApi, 'getApi').and.returnValue(api);
        spyOn(zemGridEndpointApiConverter, 'convertField').and.callThrough();

        var metaData = zemGridEndpointService.createMetaData($scope, constants.level.ACCOUNTS, 1, constants.breakdown.CAMPAIGN);
        var endpoint = zemGridEndpointService.createEndpoint(metaData);
        var promise = endpoint.saveData(value, row, column);
        $scope.$apply();

        expect(api.save).toHaveBeenCalled();
        expect(zemGridEndpointApiConverter.convertField).toHaveBeenCalled();
        expect(promise.$$state.value).toEqual({
            property: 'some property',
            value: {
                valueProperty: value
            }
        });
    });
});
