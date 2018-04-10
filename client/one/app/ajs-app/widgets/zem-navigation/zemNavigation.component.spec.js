describe('ZemNavigationCtrl', function () {
    var ctrl;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function ($rootScope, $componentController) {
        var scope = $rootScope.$new();
        var element = angular.element('<div></div>');
        var locals = {$scope: scope, $element: element};
        ctrl = $componentController('zemNavigation', locals, {});

    }));

    it('should provide correct class based on type', function () {
        var item = {
            data: {},
            type: constants.entityType.ACCOUNT,
        };
        expect(ctrl.getItemClasses(item)).toEqual(
            ['zem-navigation__item--account']
        );

        ctrl.activeEntity = item;
        item.type = constants.entityType.CAMPAIGN;
        expect(ctrl.getItemClasses(item)).toEqual(
            ['zem-navigation__item--active', 'zem-navigation__item--campaign']
        );

        ctrl.selectedEntity = item;
        expect(ctrl.getItemClasses(item)).toEqual(
            ['zem-navigation__item--active', 'zem-navigation__item--selected', 'zem-navigation__item--campaign']
        );

        ctrl.activeEntity = null;
        expect(ctrl.getItemClasses(item)).toEqual(
            ['zem-navigation__item--selected', 'zem-navigation__item--campaign']
        );

        item.type = constants.entityType.AD_GROUP;
        item.data.archived = true;
        expect(ctrl.getItemClasses(item)).toEqual(
            ['zem-navigation__item--archived', 'zem-navigation__item--selected', 'zem-navigation__item--group']
        );


    });

    it('should provide correct icon based on state', function () {
        var item = {
            data: {},
            type: constants.entityType.ACCOUNT,
        };
        expect(ctrl.getItemIconClass(item)).toEqual('zem-navigation__item-icon--none');

        item.type = constants.entityType.AD_GROUP;
        expect(ctrl.getItemIconClass(item)).toEqual('zem-navigation__item-icon--active');

        item.data.active = constants.infoboxStatus.STOPPED;
        expect(ctrl.getItemIconClass(item)).toEqual('zem-navigation__item-icon--stopped');

        item.data.active = constants.infoboxStatus.INACTIVE;
        expect(ctrl.getItemIconClass(item)).toEqual('zem-navigation__item-icon--inactive');

        item.data.active = constants.infoboxStatus.AUTOPILOT;
        expect(ctrl.getItemIconClass(item)).toEqual('zem-navigation__item-icon--autopilot');

        item.data.active = constants.infoboxStatus.LANDING_MODE;
        expect(ctrl.getItemIconClass(item)).toEqual('zem-navigation__item-icon--landing');

        item.data.active = constants.infoboxStatus.CAMPAIGNSTOP_LOW_BUDGET;
        expect(ctrl.getItemIconClass(item)).toEqual('zem-navigation__item-icon--active');

        item.data.active = constants.infoboxStatus.CAMPAIGNSTOP_STOPPED;
        expect(ctrl.getItemIconClass(item)).toEqual('zem-navigation__item-icon--stopped');

        item.data.active = constants.infoboxStatus.CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE;
        expect(ctrl.getItemIconClass(item)).toEqual('zem-navigation__item-icon--active');

        item.data.active = constants.infoboxStatus.CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE_PRICE_DISCOVERY;
        expect(ctrl.getItemIconClass(item)).toEqual('zem-navigation__item-icon--active');

        item.data.active = constants.infoboxStatus.CAMPAIGNSTOP_PENDING_BUDGET_AUTOPILOT;
        expect(ctrl.getItemIconClass(item)).toEqual('zem-navigation__item-icon--autopilot');
    });
});
