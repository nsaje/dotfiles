/* global module,beforeEach,it,describe,expect,inject */
'use strict';

describe('CampaignCtrl', function () {
    var $scope, parentScope, $state, user, api;

    beforeEach(function () {
        module('one');

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
