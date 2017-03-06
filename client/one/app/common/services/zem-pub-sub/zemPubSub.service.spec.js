describe('zemPubSubService', function () {
    var pubSub;

    beforeEach(module('one'));
    beforeEach(module('one.mocks.zemInitializationService'));
    beforeEach(inject(function (_zemPubSubService_) {
        pubSub = _zemPubSubService_.createInstance();
    }));

    it ('should call registered handler', function () {
        var testHandler = jasmine.createSpy();
        pubSub.register('test', testHandler);
        expect(testHandler).not.toHaveBeenCalled();

        pubSub.notify('test', {});
        expect(testHandler).toHaveBeenCalled();
    });
});
