describe('component: zemHeaderBreadcrumb', function () {
    var $document;
    var $componentController;
    var zemPermissions;
    var ctrl;
    var zemNavigationNewService;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(angular.mock.module('one.mocks.zemPermissions'));
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
            expect($document[0].title).toEqual('My accounts | Zemanta');

            zemPermissions.setMockedPermissions('zemauth.can_see_all_accounts');
            callback(null);
            expect($document[0].title).toEqual('All accounts | Zemanta');

            var activeEntity = {
                name: 'Account XY',
                type: constants.entityType.ACCOUNT,
            };
            zemNavigationNewService.getActiveEntity.and.returnValue(activeEntity);
            callback({}, activeEntity);
            expect($document[0].title).toEqual('Account XY | Zemanta');
        });

        it('should update breadcrumb on entity update', function () {
            var myAccountsBreadcrumb = {
                name: 'My accounts',
                typeName: 'Home',
                href: '/v2/analytics/accounts'
            };

            callback(null);
            expect(ctrl.breadcrumb).toEqual([myAccountsBreadcrumb]);

            var account = {
                id: 10,
                name: 'Account XY',
                type: constants.entityType.ACCOUNT,
            };

            var campaign = {
                id: 20,
                name: 'Campaign XY',
                type: constants.entityType.CAMPAIGN,
                parent: account,
            };

            zemNavigationNewService.getActiveEntity.and.returnValue(account);
            callback({}, account);
            expect(ctrl.breadcrumb).toEqual([
                myAccountsBreadcrumb,
                {
                    name: 'Account XY',
                    typeName: 'Account',
                    href: '/v2/analytics/account/10'
                }
            ]);

            zemNavigationNewService.getActiveEntity.and.returnValue(campaign);
            callback({}, campaign);
            expect(ctrl.breadcrumb).toEqual([
                myAccountsBreadcrumb,
                {
                    name: 'Account XY',
                    typeName: 'Account',
                    href: '/v2/analytics/account/10'
                }, {
                    name: 'Campaign XY',
                    typeName: 'Campaign',
                    href: '/v2/analytics/campaign/20'
                }
            ]);
        });
    });
});
