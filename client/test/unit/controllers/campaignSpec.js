/* global module,beforeEach,it,describe,expect,inject */
'use strict';

describe('CampaignCtrl', function () {
    var $scope, parentScope, $state, user, api, zemServiceMock, zemFilterServiceMock;

    beforeEach(function () {
        module('one');

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

            zemFilterServiceMock = {
                getShowArchived: function () {
                    return true;
                },
                getFilteredSources: function () {},
                getFilteredAccountTypes: function () {},
                getFilteredAgencies: function () {},
            };

            $provide.value('zemFilterService', zemFilterServiceMock);
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

            user = {
                permissions: {},
            };

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

            zemLocalStorageService.init(user);
            $controller('MainCtrl', {
                $scope: parentScope,
                $state: $state,
                user: user,
                accountsAccess: {
                    hasAccounts: true,
                },
                zemFullStoryService: {identify: function () {}},
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

    it('inits models propery', function () {
        $scope.getContentInsights();
        expect($scope.contentInsights).toEqual({
            metric: 'ctr',
            summary: 'title',
            rows: [],
        });
    });
});
