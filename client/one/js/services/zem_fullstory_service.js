/*globals FS*/
'use strict';

oneApp.factory('zemFullStoryService', function() {
    function identify(user) {
        var email = user.email;
        if (typeof FS === 'undefined') {
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
