describe('component: zemPublisherGroups', function() {
    var $ctrl;
    var zemPublisherGroupsEndpoint;
    var mockedUser;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function(
        $componentController,
        _zemPublisherGroupsEndpoint_,
        zemUserService
    ) {
        zemPublisherGroupsEndpoint = _zemPublisherGroupsEndpoint_;
        var bindings = {
            account: {
                id: 1,
            },
            agency: {
                id: 7,
            },
        };
        $ctrl = $componentController('zemPublisherGroups', {}, bindings);
        mockedUser = {agencies: []};
        spyOn(zemUserService, 'current').and.callFake(function() {
            return mockedUser;
        });
    }));

    it('should initialize without errors', function() {
        spyOn(zemPublisherGroupsEndpoint, 'list').and.callThrough();
        $ctrl.$onInit();

        expect(zemPublisherGroupsEndpoint.list).toHaveBeenCalled();
    });

    it('should call download', function() {
        spyOn(zemPublisherGroupsEndpoint, 'download').and.callThrough();
        $ctrl.download(2);

        expect(zemPublisherGroupsEndpoint.download).toHaveBeenCalledWith(
            1,
            7,
            2
        );
    });
});
