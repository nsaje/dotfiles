describe('zemPermissions', function() {
    var zemPermissions;
    var mockedUser;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function(
        _$rootScope_,
        $q,
        zemUserService,
        _zemPermissions_
    ) {
        zemPermissions = _zemPermissions_;
        mockedUser = {
            id: 123,
            permissions: {
                permission: true,
                anotherPermission: true,
                internalPermission: false,
            },
            email: 'test@zemanta.com',
            agencies: [],
        };
        spyOn(zemUserService, 'current').and.callFake(function() {
            return mockedUser;
        });
    }));

    describe('hasPermission:', function() {
        it('should return false if called without specifying permission', function() {
            expect(zemPermissions.hasPermission()).toBe(false);
        });

        it('should return true if user has the specified permission', function() {
            expect(zemPermissions.hasPermission('permission')).toBe(true);
        });

        it('should return true if user has all the specified permissions', function() {
            expect(
                zemPermissions.hasPermission([
                    'permission',
                    'anotherPermission',
                ])
            ).toBe(true);
        });

        it('should return false if user does not have the specified permission', function() {
            expect(zemPermissions.hasPermission('unavailablePermission')).toBe(
                false
            );
        });

        it('should return false if user does not have all the specified permissions', function() {
            expect(
                zemPermissions.hasPermission([
                    'permission',
                    'unavailablePermission',
                ])
            ).toBe(false);
        });
    });

    describe('hasPermissionBCMv2:', function() {
        it('should return false if called without specifying permission', function() {
            expect(zemPermissions.hasPermissionBCMv2()).toBe(false);
        });

        it('should return true if user has the specified permission', function() {
            expect(zemPermissions.hasPermissionBCMv2('permission')).toBe(true);
        });

        it('should return true if user has all the specified permissions', function() {
            expect(
                zemPermissions.hasPermissionBCMv2([
                    'permission',
                    'anotherPermission',
                ])
            ).toBe(true);
        });

        it('should return false if user does not have the specified permission', function() {
            expect(
                zemPermissions.hasPermissionBCMv2('unavailablePermission')
            ).toBe(false);
        });

        it('should return false if user does not have all the specified permissions', function() {
            expect(
                zemPermissions.hasPermissionBCMv2([
                    'permission',
                    'unavailablePermission',
                ])
            ).toBe(false);
        });

        it('should return true if user does not have platform_cost_breakdown permission but we are in non-bcm-v2 mode', function() {
            // eslint-disable-line max-len
            mockedUser.permissions[
                'zemauth.can_view_platform_cost_breakdown'
            ] = false;
            expect(
                zemPermissions.hasPermissionBCMv2(
                    'zemauth.can_view_platform_cost_breakdown',
                    false
                )
            ).toBe(true);
        });

        it('should return false if user does not have platform_cost_breakdown permission and we are in bcm-v2 mode', function() {
            // eslint-disable-line max-len
            mockedUser.permissions[
                'zemauth.can_view_platform_cost_breakdown'
            ] = false;
            expect(
                zemPermissions.hasPermissionBCMv2(
                    'zemauth.can_view_platform_cost_breakdown',
                    true
                )
            ).toBe(true);
        });
    });

    describe('isPermissionInternal:', function() {
        it('should return false if called without specifying permission', function() {
            expect(zemPermissions.isPermissionInternal()).toBe(false);
        });

        it('should return false if specified permission is not internal', function() {
            expect(zemPermissions.isPermissionInternal('permission')).toBe(
                false
            );
        });

        it('should return true if specified permission is internal', function() {
            expect(
                zemPermissions.isPermissionInternal('internalPermission')
            ).toBe(true);
        });
    });

    describe('hasAgencyScope:', function() {
        it("should return false if user doesn't have agency scope for specified agency", function() {
            mockedUser.agencies = ['5', '7'];
            expect(zemPermissions.hasAgencyScope('9')).toBe(false);
        });

        it('should return true if user has agency scope for specified agency', function() {
            mockedUser.agencies = ['5', '7'];
            expect(zemPermissions.hasAgencyScope('5')).toBe(true);
        });
    });
});
