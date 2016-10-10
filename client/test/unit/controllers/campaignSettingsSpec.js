/* global describe,beforeEach,module,it,inject,expect,spyOn */
'use strict';

describe('CampaignSettingsCtrl', function () {
    var $scope, $state, $q, api;
    var zemCampaignService;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(function () {
        inject(function ($rootScope, $controller, _$state_, _$q_, _zemCampaignService_) {
            $q = _$q_;
            zemCampaignService = _zemCampaignService_;
            $scope = $rootScope.$new();
            $scope.setActiveTab = function () {};
            $state = _$state_;
            $state.params = {id: 1};

            $controller('CampaignSettingsCtrl', {$scope: $scope});
        });
    });

    describe('saveSettings', function () {
        it('calls api with settings and goals', function () {
            var deferred = $q.defer();
            $scope.settings = {id: 1, data: 'settings'};
            $scope.campaignGoalsDiff = 'goals-diff';

            spyOn (zemCampaignService, 'update').and.callFake(function () {
                return deferred.promise;
            });

            $scope.saveSettings();

            expect(zemCampaignService.update).toHaveBeenCalled();
            expect(zemCampaignService.update).toHaveBeenCalledWith(1,
                {
                    settings: {id: 1, data: 'settings'},
                    goals: 'goals-diff'
                });
        });
    });

    describe('getGaTrackingTypeByValue', function () {
        it('returns correct tracking type by value', function () {
            var type = $scope.getGaTrackingTypeByValue(constants.gaTrackingType.EMAIL);
            expect(type).toEqual({name: 'Email', value: 1});
        });

        it('returns undefined when matching type does not exist', function () {
            var type = $scope.getGaTrackingTypeByValue(999);
            expect(type).toBeUndefined();
        });
    });
});
