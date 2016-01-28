'use strict';

describe('zemFileInput', function () {
    var parentElement, element, inputElement;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(inject(function ($compile, $rootScope) {
        parentElement = $compile('<div><div zem-file-input="file" /></div>')($rootScope);
        element = parentElement.find('[zem-file-input]');
        inputElement = parentElement.find('input[type=file]');
    }));

    it('creates file input element and ads it to DOM', function () {
        expect(inputElement[0]).toBeDefined();
    });

    it('trigger click event on file input when clicked', function () {
        var handler = jasmine.createSpy('handler');
        inputElement.bind('click', handler);

        element.trigger('click');

        expect(handler).toHaveBeenCalled();
    });
});
