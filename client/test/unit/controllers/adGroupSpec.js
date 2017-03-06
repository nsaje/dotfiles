'use strict';

describe('AdGroupCtrl', function () {
    var $scope, parentScope, $state, api;

    beforeEach(module('one'));
    beforeEach(module('one.mocks.zemInitializationService'));
    beforeEach(function () {
        module(function ($provide) {
            var mockApiFunc = function () {
                return {
                    then: function () {
                        return {
                            finally: function () {
                            },
                        };
                    },
                    abort: function () {
                    },
                };
            };

            api = {
                navigation: {
                    list: mockApiFunc,
                },
            };

            $provide.value('api', api);
        });

        inject(function ($rootScope, $controller, _$state_, zemLocalStorageService) {
            parentScope = $rootScope.$new();
            $scope = parentScope.$new();

            $scope.adGroupData = {};

            $state = _$state_;
            $state.params.id = 1;

            $controller('MainCtrl', {
                $scope: parentScope,
                $state: $state,
                accountsAccess: {
                    hasAccounts: true,
                },
                zemFullStoryService: {identifyUser: function () {}}
            });
            $controller('AdGroupCtrl', {
                $scope: $scope,
                $state: $state,
                adGroupData: {
                    account: {
                        id: 4,
                    },
                    campaign: {
                        id: 2,
                    },
                    adGroup: {
                        id: 3,
                    },
                },
            });
        });
    });

    it('inits models propery', function () {
        expect($scope.adGroup.id, 3);
        expect($scope.campaign.id, 2);
        expect($scope.account.id, 4);
    });

    it('hides Content Ads+ tab when no permission', function () {
        var tabs = $scope.getTabs();
        expect(tabs.length).toEqual(4);
    });

    describe('setAdGroupData', function () {
        it('should add key-value pair for the current ad group', function () {
            $scope.adGroupData = {1: {key1: 'value1'}};
            $scope.setAdGroupData('key2', 'value2');
            expect($scope.adGroupData).toEqual({
                1: {
                    key1: 'value1',
                    key2: 'value2'
                }
            });
        });

        it('should store key-value pair for the current ad group even when nothing has been stored yet', function () {
            $scope.adGroupData = {};
            $scope.setAdGroupData('key2', 'value2');
            expect($scope.adGroupData).toEqual({
                1: {
                    key2: 'value2'
                }
            });
        });
    });
});
