describe('zemFacebookPage', function () {
    var $scope;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(inject(function ($compile, $rootScope) {
        var template = '<zem-facebook-page zem-has-permission="hasPermission" zem-is-permission-internal="isPermissionInternal" zem-config="config" zem-account-id="settings.id" zem-facebook-page="settings.facebookPage" zem-facebook-status="settings.facebookStatus" zem-facebook-page-errors="errors.facebookPage" zem-facebook-page-changed="facebookPage.changed">';
        
        $scope = $rootScope.$new();
        
        
    }));

    // it('creates file input element and ads it to DOM', function () {
    //     expect(inputElement[0]).toBeDefined();
    // });
    //
    // it('trigger click event on file input when clicked', function () {
    //     var handler = jasmine.createSpy('handler');
    //     inputElement.bind('click', handler);
    //
    //     element.trigger('click');
    //
    //     expect(handler).toHaveBeenCalled();
    // });
});
