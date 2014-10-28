/*globals FS*/
'use strict';

oneApp.factory('zemFullStoryService', function() {
    function identify(user) {
        FS.identify(user.email, {email: user.email});
    }

    return {
        identify: identify
    };
});
