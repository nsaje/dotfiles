'use strict';

describe('MainCtrl', function () {
    var $scope;
    var ctrl;
    var $state;
    var user = { permissions: [] };
    var accounts;
    var zemFullStoryService;

    beforeEach(function () {
        module('one');

        module(function ($provide) {
            $provide.value('zemMoment', function () {
                return moment('2013-02-08T09:30:26.123+01:00');
            });
        });


        inject(function ($rootScope, $controller, _$state_) {
            $scope = $rootScope.$new();
            $state = _$state_;
            zemFullStoryService = {identify: function(user) {}};

            spyOn(zemFullStoryService, 'identify');

            ctrl = $controller('MainCtrl', {$scope: $scope, $state: $state, user: user, accounts: accounts, zemFullStoryService: zemFullStoryService});
        });
    });

    it('should init accounts properly', function () {
        expect($scope.accounts).toEqual(accounts);
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
