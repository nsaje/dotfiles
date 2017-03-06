angular.module('one.views').controller('zemMainView', function (zemPermissions) {
    var $ctrl = this;

    initialize();

    function initialize () {
        $ctrl.hasPermission = zemPermissions.hasPermission;
    }
});
