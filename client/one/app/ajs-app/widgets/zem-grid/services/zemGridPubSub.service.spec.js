describe('zemGridPubSub', function() {
    var $rootScope;
    var zemGridPubSub;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(angular.mock.module('one.mocks.NgZone'));

    beforeEach(inject(function(_$rootScope_, _zemGridPubSub_) {
        $rootScope = _$rootScope_;
        zemGridPubSub = _zemGridPubSub_;
    }));

    it('should notify listeners based on the registered event', function() {
        var scope = $rootScope.$new();
        var pubsub = zemGridPubSub.createInstance(scope);

        var spyOnMetaDataUpdate = jasmine.createSpy();
        var spyOnDataUpdate = jasmine.createSpy();
        pubsub.register(
            pubsub.EVENTS.METADATA_UPDATED,
            null,
            spyOnMetaDataUpdate
        );
        pubsub.register(pubsub.EVENTS.DATA_UPDATED, null, spyOnDataUpdate);

        var metaData = {};
        var data = {};
        pubsub.notify(pubsub.EVENTS.METADATA_UPDATED, metaData);
        pubsub.notify(pubsub.EVENTS.DATA_UPDATED, data);

        expect(spyOnMetaDataUpdate).toHaveBeenCalledWith(
            jasmine.any(Object),
            metaData
        );
        expect(spyOnDataUpdate).toHaveBeenCalledWith(jasmine.any(Object), data);
    });
});
