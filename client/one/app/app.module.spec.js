// zemSpecsHelper provides helper functions for specs/tests;
// e.g. mocking permission services, mocking initialization and http requests, etc.

var zemSpecsHelper = new zemSpecsHelperProvider(); // eslint-disable-line no-unused-vars
function zemSpecsHelperProvider () {
    //
    //  Public API
    //
    this.provideMockedPermissionsService = provideMockedPermissionsService;
    this.mockUserInitialization = mockUserInitialization;
    this.getMockedAsyncFunction = getMockedAsyncFunction;

    //
    // Internal
    //
    var testUser = {
        id: 1,
        name: 'Mock User',
        email: 'mock@user.com',
        permissions: [], // zemPermissions mocked
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
        $httpBackend.whenGET(/^\/api\/.*\/nav\//).respond(200, {data: {}});
    }

    function getMockedAsyncFunction ($injector, data, reject) {
        return function () {
            var $q = $injector.get('$q');
            var deferred = $q.defer();
            if (reject) {
                deferred.reject(data);
            } else {
                deferred.resolve(data);
            }
            return deferred.promise;
        };
    }
}
