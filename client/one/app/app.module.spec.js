// zemSpecsHelper provides helper functions for specs/tests;
// e.g. mocking permission services, mocking initialization and http requests, etc.

var zemSpecsHelper = new zemSpecsHelperProvider(); // eslint-disable-line no-unused-vars
function zemSpecsHelperProvider () {
    //
    //  Public API
    //
    this.provideMockedPermissionsService = provideMockedPermissionsService;
    this.mockUserInitialization = mockUserInitialization;

    //
    // Internal
    //
    var testUser = {
        id: 1,
        name: 'Mock User',
        email: 'mock@user.com',
        permissions: [] // zemPermissions mocked
    };

    function provideMockedPermissionsService ($provide) {
        $provide.value('zemPermissions', {
            hasPermission: function () { return true; },
            isPermissionInternal: function () { return false; },
        });
    }

    function mockUserInitialization ($injector) {
        var $httpBackend = $injector.get('$httpBackend');
        $httpBackend.whenGET('/api/users/current/').respond(200, {
            data: {
                user: testUser
            }
        });
        $httpBackend.whenGET('/api/all_accounts/nav/').respond(200, {data: {}});
        $httpBackend.flush();
    }
}
