describe('zemFacebookPage', function () {
    const FACEBOOK_PAGE = 'http://www.facebook.com/zemanta';
    const FACEBOOK_STATUS_CONNECTED = 'Connected';

    var $scope, zemFacebookPageElement, isolate, inputElement;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(inject(function ($compile, $rootScope, $httpBackend, $q, api) {
        var template = '<zem-facebook-page zem-has-permission="hasPermission" zem-is-permission-internal="isPermissionInternal" zem-config="config" zem-account-id="settings.id" zem-facebook-page="settings.facebookPage" zem-facebook-status="settings.facebookStatus" zem-facebook-page-errors="errors.facebookPage" zem-facebook-page-changed="facebookPage.changed">';
        
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

        api.accountSettings.getFacebookAccountStatus = function () {
            var deferred = $q.defer();
            deferred.resolve({data: {status: FACEBOOK_STATUS_CONNECTED}});
            return deferred.promise;
        };

        zemFacebookPageElement = $compile(template)($scope);
        $scope.$digest();
        isolate = zemFacebookPageElement.isolateScope();

        inputElement = zemFacebookPageElement.find('input[type=text]');
    }));

    it('creates Facebook page control and ads it to DOM', function () {
        expect(zemFacebookPageElement[0]).toBeDefined();
        expect(inputElement[0]).toBeDefined();
    });
    
    /*it('updates the Facebook status when the Facebook page is inserted', function () {
        inputElement.val(FACEBOOK_PAGE).trigger('input');
        $scope.$digest();
        expect($scope.settings.facebookPage).toEqual(FACEBOOK_PAGE);
        expect($scope.settings.facebookStatus).toEqual(FACEBOOK_STATUS_CONNECTED);
    });*/
});
