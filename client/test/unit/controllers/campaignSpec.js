/* global module,beforeEach,it,describe,expect,inject */
'use strict';

describe('CampaignCtrl', function () {
    var $scope, parentScope, $state, api, zemServiceMock;

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

            $scope.campaignData = {};
            $scope.hasPermission = function () {
                return true;
            };

            $state = _$state_;
            $state.params.id = 1;

            var mockApiFunc = function () {
                return {
                    then: function (dataFunc) {
                        dataFunc({
                            metric: 'ctr',
                            summary: 'title',
                            rows: [],
                        });
                    },
                };
            };

            api = {
                campaignContentInsights: {
                    get: mockApiFunc,
                },
            };

            $controller('MainCtrl', {
                $scope: parentScope,
                $state: $state,
                accountsAccess: {
                    hasAccounts: true,
                },
                zemFullStoryService: {identifyUser: function () {}},
            });
            $controller('CampaignCtrl', {
                $scope: $scope,
                $state: $state,
                campaignData: {
                    id: 1,
                    name: 'Test Campaign',
                    archived: false,
                    landingMode: false,
                },
                api: api,
            });
        });
    });
});

