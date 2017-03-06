describe('component: zemPublisherGroups', function () {
    var $ctrl;
    var zemPublisherGroupsEndpoint;

    beforeEach(module('one'));
    beforeEach(module('one.mocks.zemInitializationService'));

    beforeEach(inject(function ($componentController, _zemPublisherGroupsEndpoint_) {
        zemPublisherGroupsEndpoint = _zemPublisherGroupsEndpoint_;
        var bindings = {
            account: {
                id: 1
            }
        };
        $ctrl = $componentController('zemPublisherGroups', {}, bindings);
    }));

    it('should initialize without errors', function () {
        spyOn(zemPublisherGroupsEndpoint, 'list').and.callThrough();
        $ctrl.$onInit();

        expect(zemPublisherGroupsEndpoint.list).toHaveBeenCalled();
    });

    it('should call download', function () {
        spyOn(zemPublisherGroupsEndpoint, 'download').and.callThrough();
        $ctrl.download(2);

        expect(zemPublisherGroupsEndpoint.download).toHaveBeenCalledWith(1, 2);
    });
});
