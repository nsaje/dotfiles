describe('zemFileInput', function() {
    var element, buttonElement, inputElement;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(angular.mock.module('stateMock'));

    beforeEach(inject(function($compile, $rootScope) {
        element = $compile(
            '<zem-file-input zem-file-input-callback="callback" zem-file-input-accept="image/*">' +
                '<button zem-file-input-trigger></button></zem-file-input>/>'
        )($rootScope);
        buttonElement = element.find('button');
        inputElement = element.find('input[type=file]');
    }));

    it('creates file input element and ads it to DOM', function() {
        expect(inputElement[0]).toBeDefined();
        expect(inputElement.attr('accept')).toBe('image/*');
    });

    it('trigger click event on file input when clicked', function() {
        var handler = jasmine.createSpy('handler');
        inputElement.bind('click', handler);
        buttonElement.trigger('click');
        expect(handler).toHaveBeenCalled();
    });
});
