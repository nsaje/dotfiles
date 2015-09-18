/*globals Intercom*/
'use strict';

oneApp.factory('zemIntercomService', ['$window', function($window) {
    var INTERCOM_APP_ID = 'anyekw96';

    function boot(user) {
        var userDict, companyObject;
        if ($window.Intercom === undefined) {
            return;
        }

        userDict = {
            app_id: INTERCOM_APP_ID,
            name: user.name,
            email: user.email
        };

        companyObject = getCompanyObjectFromEmail(user.email);
        if (companyObject){
            userDict['company'] = companyObject;
        }

        $window.Intercom('boot',userDict);
    }

    function getCompanyObjectFromEmail(email) {
        var splitEmail = email.split('@'), companyName;
        if (splitEmail.length !== 2) {
            return false;
        }
        companyName = splitEmail[1];
        return {
            id: companyName,
            name: companyName
        };
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
