describe('zemUserService', function () {
    var $rootScope;
    var zemUserService;
    var mockedUser = {
        id: 123,
        permissions: {
            permission: true,
            internalPermission: false,
        },
        email: 'test@zemanta.com',
    };

    beforeEach(module('one'));
    beforeEach(inject(function (_$rootScope_, $q, _zemUserService_, zemUserEndpoint) {
        $rootScope = _$rootScope_;
        zemUserService = _zemUserService_;

        spyOn(zemUserEndpoint, 'loadUser').and.callFake(function () {
            var deferred = $q.defer();
            deferred.resolve(mockedUser);
            return deferred.promise;
        });
    }));
    beforeEach(function (done) {
        zemUserService.init().then(done);
        $rootScope.$apply();
    });

    it('should correctly initialize with user data fetched from user endpoint', function () {
        expect(zemUserService.getUser()).toEqual(mockedUser);
    });

    describe('userHasPermissions:', function () {
        it('should return false if called without specifying permission', function () {
            expect(zemUserService.userHasPermissions()).toBe(false);
        });

        it('should return true if user has the specified permission', function () {
            expect(zemUserService.userHasPermissions('permission')).toBe(true);
        });

        it('should return false if user does not have the specified permission', function () {
            expect(zemUserService.userHasPermissions('unavailablePermission')).toBe(false);
        });
    });

    describe('isPermissionInternal:', function () {
        it('should return false if called without specifying permission', function () {
            expect(zemUserService.isPermissionInternal()).toBe(false);
        });

        it('should return false if specified permission is not internal', function () {
            expect(zemUserService.isPermissionInternal('permission')).toBe(false);
        });

        it('should return true if specified permission is internal', function () {
            expect(zemUserService.isPermissionInternal('internalPermission')).toBe(true);
        });
    });

    describe('getUserId:', function () {
        it('should return correct user id', function () {
            expect(zemUserService.getUserId()).toEqual(123);
        });
    });

    describe('getUserEmail:', function () {
        it('should return correct user email', function () {
            expect(zemUserService.getUserEmail()).toEqual('test@zemanta.com');
        });
    });
});
