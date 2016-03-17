/* global describe,angular,beforeEach,module,it,inject,expect,spyOn */
'use strict';

describe('CampaignSettingsCtrl', function () {
    var $modalStack, $scope, $state, $q, api;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(function () {
        inject(function ($rootScope, $controller, _$state_, _$q_, _$modalStack_) {
            $q = _$q_;
            $scope = $rootScope.$new();
            $scope.setActiveTab = function () {};

            var mockApiFunc = function () {
                return {
                    then: function () {
                        return {
                            finally: function () {}
                        };
                    }
                };
            };

            api = {
                campaignSettings: {
                    get: mockApiFunc,
                    save: mockApiFunc
                }
            };

            $state = _$state_;
            $state.params = {id: 1};

            $modalStack = _$modalStack_;

            $controller('CampaignSettingsCtrl', {$scope: $scope, api: api});
        });
    });

    describe('saveSettings', function () {
        it('calls api with settings and goals', function () {
            var deferred = $q.defer();
            $scope.settings = 'settings';
            $scope.campaignGoalsDiff = 'goals-diff';

            spyOn(api.campaignSettings, 'save').and.callFake(function () { return deferred.promise; });

            $scope.saveSettings();
            
            expect(api.campaignSettings.save).toHaveBeenCalled();
            expect(api.campaignSettings.save).toHaveBeenCalledWith('settings', 'goals-diff');
        });
    });
});
