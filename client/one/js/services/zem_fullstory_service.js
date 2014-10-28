/*globals FS*/
'use strict';

oneApp.factory('zemFullStoryService', function() {
    function identify(user) {
        FS.identify(user.id, {email: user.email});
    }

    return {
        identify: identify
    };
});
