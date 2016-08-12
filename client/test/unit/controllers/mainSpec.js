'use strict';

describe('MainCtrl', function () {
    var api;
    var $scope;
    var ctrl;
    var $state;
    var user = {permissions: []};
    var zemFullStoryService;
    var zemFilterServiceMock;
    var zemUserSettings;
    var accountsAccess;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

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

        inject(function ($rootScope, $controller, _$state_) {
            $scope = $rootScope.$new();
            $state = _$state_;

            zemFullStoryService = {identify: function (user) {}};
            zemUserSettings = {
                getInstance: function () {
                    return {
                        register: function () {},
                        registerGlobal: function () {}
                    };
                }
            };

            spyOn(zemFullStoryService, 'identify');

            accountsAccess = {
                hasAccounts: true
            };

            ctrl = $controller('MainCtrl', {
                $scope: $scope,
                $state: $state,
                api: api,
                user: user,
                accountsAccess: accountsAccess,
                zemFullStoryService: zemFullStoryService,
                zemUserSettings: zemUserSettings,
            });
        });
    });

    it('should init accounts access properly', function () {
        expect($scope.accountsAccess).toEqual(accountsAccess);
    });

    describe('hasPermission', function () {
        beforeEach(function () {
            $scope.user = {permissions: {}};
        });

        it('should return true if user has the specified permission', function () {
            $scope.user.permissions.somePermission = true;
            expect($scope.hasPermission('somePermission')).toBe(true);
        });

        it('should return false if user does not have the specified permission', function () {
            expect($scope.hasPermission('somePermission')).toBe(false);
        });

        it('should return false if called without specifying permission', function () {
            expect($scope.hasPermission()).toBe(false);
        });

        it('should identify user with FullStory', function () {
            expect(zemFullStoryService.identify).toHaveBeenCalledWith(user);
        });
    });
});
