describe('zemDropdownSelect', function() {
    var $scope, element, isolate;

    var template =
        '<zem-dropdown-select zem-placeholder="Test" zem-disabled-title="Disabled title" ' +
        'zem-on-select="onSelectTest(selected)" zem-check-disabled="checkDisabledTest()" ' +
        'zem-dropdown-select-options="options">' +
        '</zem-dropdown-select>';

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($compile, $rootScope) {
        $scope = $rootScope.$new();

        $scope.onSelectTest = function() {};
        $scope.disabled = false;
        $scope.checkDisabledTest = function() {
            return $scope.disabled;
        };
        $scope.options = [
            {
                name: 'D1',
                value: 'd1',
                hasPermission: true,
                disabled: false,
                notification: undefined,
            },
            {
                name: 'D2',
                value: 'd2',
                hasPermission: true,
                disabled: false,
                notification: 'Notification D2',
            },
        ];

        element = $compile(template)($scope);

        $scope.$digest();
        isolate = element.isolateScope();
    }));

    it('fires onSelect', function() {
        spyOn($scope, 'onSelectTest');

        isolate.selectedItem = 'd1';
        isolate.callOnSelect();

        expect($scope.onSelectTest).toHaveBeenCalledWith('d1');
    });

    it('adds popover when disabled', function() {
        $scope.disabled = true;
        $scope.$digest();

        expect(isolate.disabledTitleOrUndefined).toBeDefined();

        $scope.disabled = false;
        $scope.$digest();

        expect(isolate.disabledTitleOrUndefined).not.toBeDefined();
    });
});
