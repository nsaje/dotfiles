'use strict';

describe('CampaignAgencyCtrl', function () {
    var $modalStack, $scope, $state, $q, api;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(function () {
        inject(function ($rootScope, $controller, _$state_, _$q_, _$modalStack_) {
            $q = _$q_;
            $scope = $rootScope.$new();

            var mockApiFunc = function() {
                return {
                    then: function() {
                        return {
                            finally: function() {}
                        };
                    }
                };
            };

            api = {
                campaignAgency: {
                    get: mockApiFunc
                }
            };

            $state = _$state_;
            $state.params = {id: 1};

            $modalStack = _$modalStack_;

            $controller('CampaignAgencyCtrl', {$scope: $scope, api: api});
        });
    });
});
