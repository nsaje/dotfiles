describe('zemPermissions', function () {
    var zemPermissions;
    var mockedUser = {
        id: 123,
        permissions: {
            permission: true,
            internalPermission: false,
        },
        email: 'test@zemanta.com',
    };

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function (_$rootScope_, $q, zemUserService, _zemPermissions_) {
        zemPermissions = _zemPermissions_;
        spyOn(zemUserService, 'current').and.callFake(function () {
            return mockedUser;
        });
    }));

    describe('hasPermission:', function () {
        it('should return false if called without specifying permission', function () {
            expect(zemPermissions.hasPermission()).toBe(false);
        });

        it('should return true if user has the specified permission', function () {
            expect(zemPermissions.hasPermission('permission')).toBe(true);
        });

        it('should return false if user does not have the specified permission', function () {
            expect(zemPermissions.hasPermission('unavailablePermission')).toBe(false);
        });
    });

    describe('isPermissionInternal:', function () {
        it('should return false if called without specifying permission', function () {
            expect(zemPermissions.isPermissionInternal()).toBe(false);
        });

        it('should return false if specified permission is not internal', function () {
            expect(zemPermissions.isPermissionInternal('permission')).toBe(false);
        });

        it('should return true if specified permission is internal', function () {
            expect(zemPermissions.isPermissionInternal('internalPermission')).toBe(true);
        });
    });
});
