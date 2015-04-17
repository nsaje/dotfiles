'use strict';

describe('AdGroupAdsPlusCtrl', function() {
    var $scope;

    beforeEach(module('one'));
    beforeEach(module(function ($provide) {
        $provide.value('zemLocalStorageService', {get: function(){}})
    }));

    beforeEach(inject(function($controller, $rootScope) {
        $scope = $rootScope.$new();

        $scope.isPermissionInternal = function() {return true;};
        $scope.hasPermission = function() {return true;};
        $scope.getAdGroupState = function() {};
        $scope.dateRange = {};

        $controller('AdGroupAdsPlusCtrl', {$scope: $scope});
    }));

    describe('addContentAds', function(done) {
        it('opens a modal window when called', function() {
            $scope.addContentAds().result
                .catch(function(error) {
                    expect(error).toBeUndefined();
                })
                .finally(done);
        });
    });
});
