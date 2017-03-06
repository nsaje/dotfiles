describe('ZemNavigationCtrl', function () {
    var ctrl;

    beforeEach(module('one'));
    beforeEach(module('one.mocks.zemInitializationService'));

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
        expect(ctrl.getItemClasses(item)).toEqual(['account']);

        ctrl.activeEntity = item;
        item.type = constants.entityType.CAMPAIGN;
        expect(ctrl.getItemClasses(item)).toEqual(['active', 'campaign']);

        ctrl.selectedEntity = item;
        expect(ctrl.getItemClasses(item)).toEqual(['active', 'selected', 'campaign']);

        ctrl.activeEntity = null;
        expect(ctrl.getItemClasses(item)).toEqual(['selected', 'campaign']);

        item.type = constants.entityType.AD_GROUP;
        item.data.archived = true;
        expect(ctrl.getItemClasses(item)).toEqual(['archived', 'selected', 'group']);


    });

    it('should provide correct icon based on state', function () {
        var item = {
            data: {},
            type: constants.entityType.ACCOUNT,
        };
        expect(ctrl.getItemIconClass(item)).toEqual('none');

        item.type = constants.entityType.AD_GROUP;
        expect(ctrl.getItemIconClass(item)).toEqual('active');

        item.data.active = constants.infoboxStatus.STOPPED;
        expect(ctrl.getItemIconClass(item)).toEqual('stopped');

        item.data.active = constants.infoboxStatus.INACTIVE;
        expect(ctrl.getItemIconClass(item)).toEqual('inactive');

        item.data.active = constants.infoboxStatus.AUTOPILOT;
        expect(ctrl.getItemIconClass(item)).toEqual('autopilot');

        item.data.active = constants.infoboxStatus.LANDING_MODE;
        expect(ctrl.getItemIconClass(item)).toEqual('landing');
    });
});
