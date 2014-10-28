/*globals FS*/
'use strict';

oneApp.factory('zemFullStoryService', function() {
    function identify(user) {
        var email = user.email;

        FS.identify(email, {
            displayName: email,
            email: email
        });
    }

    return {
        identify: identify
    };
});
