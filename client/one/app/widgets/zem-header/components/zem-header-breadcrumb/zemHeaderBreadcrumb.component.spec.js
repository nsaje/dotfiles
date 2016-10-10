describe('component: zemHeaderBreadcrumb', function () {
    var $document;
    var $componentController;
    var zemPermissions;
    var ctrl;
    var zemNavigationNewService;

    beforeEach(module('one'));
    beforeEach(inject(function (_$document_, _$componentController_, _zemNavigationNewService_, _zemPermissions_) {
        $document = _$document_;
        $componentController = _$componentController_;
        zemPermissions = _zemPermissions_;
        zemNavigationNewService = _zemNavigationNewService_;

        var locals = {zemNavigationNewService: zemNavigationNewService};
        ctrl = $componentController('zemHeaderBreadcrumb', locals, {});
    }));

    it('should listen to navigation updated', function () {
        spyOn(zemNavigationNewService, 'onActiveEntityChange');
        ctrl.$onInit();
        expect(zemNavigationNewService.onActiveEntityChange).toHaveBeenCalled();
    });

    describe('', function () {
        var callback;
        beforeEach(function () {
            spyOn(zemNavigationNewService, 'onActiveEntityChange');
            spyOn(zemNavigationNewService, 'getActiveEntity').and.returnValue(null);
            spyOn($document, 'prop').and.callThrough();
            ctrl.$onInit();
            callback = zemNavigationNewService.onActiveEntityChange.calls.first().args[0];
        });

        it('should update document title on entity update', function () {
            callback(null);
            expect($document[0].title).toEqual('My accounts');

            spyOn(zemPermissions, 'hasPermission').and.returnValue(true);
            callback(null);
            expect($document[0].title).toEqual('All accounts');

            callback({}, {
                name: 'Account XY',
                type: constants.entityType.ACCOUNT,
            });
            expect($document[0].title).toEqual('Account XY | Zemanta');
        });

        it('should update breadcrumb on entity update', function () {
            callback(null);
            expect(ctrl.breadcrumb).toEqual([]);

            var account = {
                name: 'Account XY',
                type: constants.entityType.ACCOUNT,
            };

            var campaign = {
                name: 'Campaign XY',
                type: constants.entityType.CAMPAIGN,
                parent: account,
            };

            callback({}, account);
            expect(ctrl.breadcrumb).toEqual([{
                name: 'Account XY',
                typeName: 'Account',
                entity: jasmine.any(Object),
            }]);

            callback({}, campaign);
            expect(ctrl.breadcrumb).toEqual([{
                name: 'Account XY',
                typeName: 'Account',
                entity: jasmine.any(Object),
            }, {
                name: 'Campaign XY',
                typeName: 'Campaign',
                entity: jasmine.any(Object),
            }]);
        });
    });
});
