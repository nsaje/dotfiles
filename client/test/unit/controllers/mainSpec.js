'use strict';

describe('MainCtrl', function () {
    var $scope;
    var ctrl;
    var $state;
    var user = { permissions: [] };
    var accounts;
    var zemFullStoryService;
    var zemUserSettings;

    beforeEach(function () {
        module('one');

        inject(function ($rootScope, $controller, _$state_) {
            $scope = $rootScope.$new();
            $state = _$state_;
            zemFullStoryService = {identify: function(user) {}};
            zemUserSettings = {
                getInstance: function() {
                    return {
                        register: function() {},
                        registerGlobal: function() {}
                    };
                }
            };

            spyOn(zemFullStoryService, 'identify');

            ctrl = $controller('MainCtrl', {
                $scope: $scope,
                $state: $state,
                user: user,
                accounts: accounts,
                zemFullStoryService: zemFullStoryService,
                zemUserSettings: zemUserSettings
            });
        });
    });

    it('should init accounts properly', function () {
        expect($scope.accounts).toEqual(accounts);
    });

    describe('should default to the first account', function() {
        beforeEach(function () {
            $scope.user.permissions['zemauth.all_accounts_sources_view'] = false;
            $scope.user.permissions['zemauth.account_campaigns_view'] = true;
            $scope.accounts = [
                {
                    name: 'Test account 1',
                    archived: false,
                    id: 1
                },
                {
                    name: 'Test account 2',
                    archived: false,
                    id: 2
                }
            ];
        });

        it(function () {
            spyOn($state, 'go');
            expect($state.go).toHaveBeenCalledWith('main.accounts.campaigns', {id: 1});
        });
    });

    describe('should default to the first non archived account', function() {
        beforeEach(function () {
            $scope.user.permissions['zemauth.all_accounts_sources_view'] = false;
            $scope.user.permissions['zemauth.account_campaigns_view'] = true;
            $scope.accounts = [
                {
                    name: 'Test account 1',
                    archived: true,
                    id: 1
                },
                {
                    name: 'Test account 2',
                    archived: false,
                    id: 2
                }
            ];
        });

        it(function () {
            spyOn($state, 'go');
            expect($state.go).toHaveBeenCalledWith('main.accounts.campaigns', {id: 2});
        });
    });

    describe('hasPermission', function () {
        beforeEach(function () {
            $scope.user = { permissions: {} };
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
