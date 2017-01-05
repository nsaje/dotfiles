'use strict';

describe('MainCtrl', function () {
    var api;
    var $scope;
    var ctrl;
    var $state;
    var zemFullStoryService;
    var user;
    var zemUserServiceMock;
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

            user = {
                permissions: {},
            };

            $provide.value('api', api);
        });

        inject(function ($rootScope, $controller, _$state_, zemUserService) {
            $scope = $rootScope.$new();
            $state = _$state_;

            zemFullStoryService = {identifyUser: function (user) {}};
            zemUserSettings = {
                getInstance: function () {
                    return {
                        register: function () {},
                        registerGlobal: function () {}
                    };
                }
            };

            spyOn(zemFullStoryService, 'identifyUser');
            spyOn(zemUserService, 'current').and.returnValue(user);

            accountsAccess = {
                hasAccounts: true
            };

            ctrl = $controller('MainCtrl', {
                $scope: $scope,
                $state: $state,
                api: api,
                accountsAccess: accountsAccess,
                zemFullStoryService: zemFullStoryService,
                zemUserSettings: zemUserSettings,
            });
        });
    });

    it('should init accounts access properly', function () {
        expect($scope.accountsAccess).toEqual(accountsAccess);
    });

    it('should identify user with FullStory', function () {
        expect(zemFullStoryService.identifyUser).toHaveBeenCalledWith(user);
    });
});
