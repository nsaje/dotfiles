describe('component: zemItemScopeCell', function() {
    var $componentController;
    var $ctrl;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($injector) {
        $componentController = $injector.get('$componentController');
    }));

    it('should be correctly initialized with agency scope', function() {
        var scopedItem = {
            agencyId: '123',
            agencyName: 'Test agency',
            accountId: null,
            accountName: null,
        };
        var agencyLink = '/admin/dash/agency/123/change/';
        var bindings = {
            item: scopedItem,
            agencyLink: agencyLink,
        };

        $ctrl = $componentController('zemItemScopeCell', {}, bindings);
        $ctrl.$onInit();

        expect($ctrl.itemScopeState).toEqual(
            $ctrl.ITEM_SCOPE_STATE.agencyScope
        );
        expect($ctrl.entityName).toEqual(scopedItem.agencyName);
        expect($ctrl.canUseEntityLink).toEqual(true);
        expect($ctrl.entityLink).toEqual(agencyLink);
    });

    it('should be correctly initialized with account scope', function() {
        var scopedItem = {
            agencyId: null,
            agencyName: null,
            accountId: '123',
            accountName: 'Test account',
        };
        var accountLink = '/v2/analytics/account/123';
        var bindings = {
            item: scopedItem,
            accountLink: accountLink,
        };

        $ctrl = $componentController('zemItemScopeCell', {}, bindings);
        $ctrl.$onInit();

        expect($ctrl.itemScopeState).toEqual(
            $ctrl.ITEM_SCOPE_STATE.accountScope
        );
        expect($ctrl.entityName).toEqual(scopedItem.accountName);
        expect($ctrl.canUseEntityLink).toEqual(true);
        expect($ctrl.entityLink).toEqual(accountLink);
    });
});
