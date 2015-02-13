'use strict';

describe('AdGroupAdsPlusCtrl', function() {
    var $scope;

    beforeEach(module('one'));

    beforeEach(inject(function($controller, $rootScope) {
        $scope = $rootScope.$new();
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
