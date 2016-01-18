/*globals FS*/
'use strict';

oneApp.factory('zemFullStoryService', function () {
    function identify (user) {
        var email = user.email;

        if (window.FS === undefined) {
            return;
        }
        FS.identify(email, {
            displayName: email,
            email: email
        });
    }

    return {
        identify: identify
    };
});
