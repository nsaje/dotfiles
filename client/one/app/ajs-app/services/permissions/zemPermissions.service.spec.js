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
            mockedUser.agencies = [5, 7];
            expect(zemPermissions.hasAgencyScope('9')).toBe(false);
        });

        it('should return true if user has agency scope for specified agency', function() {
            mockedUser.agencies = [5, 7];
            expect(zemPermissions.hasAgencyScope('5')).toBe(true);
        });

        it('should return true if user has agency scope for specified agency with number input', function() {
            mockedUser.agencies = [5, 7];
            expect(zemPermissions.hasAgencyScope(5)).toBe(true);
        });
    });

    describe('canEditUsersOnAgency:', function() {
        it("should return false if the calling user is an internal user without 'user' permission", function() {
            mockedUser.entityPermissions = [
                {
                    agencyId: null,
                    accountId: null,
                    permission: 'read',
                },
            ];
            expect(zemPermissions.canEditUsersOnAgency('9')).toBe(false);
        });

        it("should return true if the calling user is an internal user with 'user' permission", function() {
            mockedUser.entityPermissions = [
                {
                    agencyId: null,
                    accountId: null,
                    permission: 'read',
                },
                {
                    agencyId: null,
                    accountId: null,
                    permission: 'user',
                },
            ];
            expect(zemPermissions.canEditUsersOnAgency('9')).toBe(true);
        });

        it("should return false if the calling user is an agency manager without 'user' permission", function() {
            mockedUser.entityPermissions = [
                {
                    agencyId: '9',
                    accountId: null,
                    permission: 'read',
                },
            ];
            expect(zemPermissions.canEditUsersOnAgency('9')).toBe(false);
        });

        it("should return true if the calling user is an agency manager with 'user' permission", function() {
            mockedUser.entityPermissions = [
                {
                    agencyId: '9',
                    accountId: null,
                    permission: 'read',
                },
                {
                    agencyId: '9',
                    accountId: null,
                    permission: 'user',
                },
            ];
            expect(zemPermissions.canEditUsersOnAgency('9')).toBe(true);
        });

        it("should return false if the calling user is an agency manager with 'user' permission on the wrong agency", function() {
            mockedUser.entityPermissions = [
                {
                    agencyId: '8',
                    accountId: null,
                    permission: 'read',
                },
                {
                    agencyId: '8',
                    accountId: null,
                    permission: 'user',
                },
            ];
            expect(zemPermissions.canEditUsersOnAgency('9')).toBe(false);
        });

        it('should return false if the calling user is an account manager', function() {
            mockedUser.entityPermissions = [
                {
                    agencyId: null,
                    accountId: '8',
                    permission: 'read',
                },
                {
                    agencyId: null,
                    accountId: '8',
                    permission: 'user',
                },
            ];
            expect(zemPermissions.canEditUsersOnAgency('9')).toBe(false);
        });
    });

    describe('canEditUsersOnAllAccounts:', function() {
        it("should return false if the calling user is an internal user without 'user' permission", function() {
            mockedUser.entityPermissions = [
                {
                    agencyId: null,
                    accountId: null,
                    permission: 'read',
                },
            ];
            expect(zemPermissions.canEditUsersOnAllAccounts()).toBe(false);
        });

        it("should return true if the calling user is an internal user with 'user' permission", function() {
            mockedUser.entityPermissions = [
                {
                    agencyId: null,
                    accountId: null,
                    permission: 'read',
                },
                {
                    agencyId: null,
                    accountId: null,
                    permission: 'user',
                },
            ];
            expect(zemPermissions.canEditUsersOnAllAccounts()).toBe(true);
        });

        it('should return false if the calling user is an agency manager', function() {
            mockedUser.entityPermissions = [
                {
                    agencyId: '8',
                    accountId: null,
                    permission: 'read',
                },
                {
                    agencyId: '8',
                    accountId: null,
                    permission: 'user',
                },
            ];
            expect(zemPermissions.canEditUsersOnAllAccounts()).toBe(false);
        });

        it('should return false if the calling user is an account manager', function() {
            mockedUser.entityPermissions = [
                {
                    agencyId: null,
                    accountId: '8',
                    permission: 'read',
                },
                {
                    agencyId: null,
                    accountId: '8',
                    permission: 'user',
                },
            ];
            expect(zemPermissions.canEditUsersOnAllAccounts()).toBe(false);
        });
    });
});
