/*globals Intercom*/
'use strict';

oneApp.factory('zemIntercomService', ['$window', function($window) {
    var INTERCOM_APP_ID = 'ixc9vxvs';

    function boot(user) {
        $window.Intercom('boot',{
              app_id: INTERCOM_APP_ID,
              name: user.name,
              email: user.email,
        });
    }

    function update() {
        if ($window.Intercom !== undefined) {
            $window.Intercom('update');
        }
    }

    return {
        boot: boot,
        update: update
    };
}]);
