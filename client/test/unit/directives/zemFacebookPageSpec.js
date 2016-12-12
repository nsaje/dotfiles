describe('zemFacebookPage', function () {
    var FACEBOOK_PAGE = 'http://www.facebook.com/zemanta';
    var FACEBOOK_STATUS_CONNECTED = 'Connected';

    var $scope, zemFacebookPageElement, isolate, inputElement;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(inject(function ($compile, $rootScope, $httpBackend, $q, zemAccountService) {
        var template = '<zem-facebook-page zem-has-permission="hasPermission" zem-is-permission-internal="isPermissionInternal" zem-config="config" zem-account-id="settings.id" zem-facebook-page-errors="errors.facebookPage" zem-facebook-page-changed="facebookPage.changed" zem-settings="settings">';

        $scope = $rootScope.$new();
        $scope.hasPermission = function () {
            return true;
        };
        $scope.isPermissionInternal = function () {
            return true;
        };
        $scope.config = {
            static_url: 'http://localhost:9999'
        };
        $scope.settings = {
            id: '123',
            facebookPage: null,
            facebookStatus: 'Empty'
        };
        $scope.errors = {};
        $scope.facebookPageChangedInfo = {
            changed: false
        };

        spyOn(zemAccountService, 'getFacebookAccountStatus').and.callFake(function () {
            var deferred = $q.defer();
            deferred.resolve({data: {status: FACEBOOK_STATUS_CONNECTED}});
            return deferred.promise;
        });

        zemFacebookPageElement = $compile(template)($scope);
        $scope.$digest();
        isolate = zemFacebookPageElement.isolateScope();

        inputElement = zemFacebookPageElement.find('input[type=text]');
    }));

    it('creates Facebook page control and ads it to DOM', function () {
        expect(zemFacebookPageElement[0]).toBeDefined();
        expect(inputElement[0]).toBeDefined();
    });
});
