describe('zemRetargeting', function() {
    var $scope, element, isolate;

    var template =
        '<zem-retargeting zem-selected-adgroup-ids="selectedAdgroupIds" zem-retargetable-adgroups="retargetableAdgroups" zem-account="account"></zem-retargeting>'; // eslint-disable-line max-len

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($compile, $rootScope) {
        $scope = $rootScope.$new();

        $scope.selectedAdgroupIds = [];
        $scope.retargetableAdgroups = [
            {
                id: 1,
                archived: false,
            },
            {
                id: 2,
                archived: true,
            },
            {
                id: 3,
                archived: false,
            },
        ];
        $scope.account = {id: 1};

        element = $compile(template)($scope);

        $scope.$digest();
        isolate = element.isolateScope();
    }));

    it('adds new ad groups', function() {
        isolate.addAdgroup({id: 1});
        $scope.$digest();
        expect($scope.selectedAdgroupIds).toEqual([1]);
        expect(isolate.availableAdgroups().length).toBe(2);
        expect(isolate.availableAdgroups()[0].id).toBe(2);

        isolate.addAdgroup({id: 3});
        $scope.$digest();
        expect($scope.selectedAdgroupIds).toEqual([1, 3]);
        expect(isolate.availableAdgroups().length).toBe(1);
    });

    it('removes selected ad groups', function() {
        $scope.selectedAdgroupIds = [1, 3];
        $scope.$digest();

        isolate.removeSelectedAdgroup({id: 1});
        $scope.$digest();
        expect($scope.selectedAdgroupIds).toEqual([3]);
        expect(isolate.availableAdgroups().length).toBe(2);
        expect(isolate.availableAdgroups()[0].id).toBe(1);

        isolate.removeSelectedAdgroup({id: 3});
        $scope.$digest();
        expect($scope.selectedAdgroupIds).toEqual([]);
        expect(isolate.availableAdgroups().length).toBe(3);
    });

    it('shows archived ad groups when enabled', function() {
        expect(isolate.availableAdgroups().length).toBe(3);
    });
});
