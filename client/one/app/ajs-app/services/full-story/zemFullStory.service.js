angular
    .module('one.services')
    .service('zemFullStoryService', function($window, zemFullStoryEndpoint) {
        // eslint-disable-line max-len
        this.identifyUser = identifyUser;
        this.allowLivestream = allowLivestream;
        this.isLivestreamAllowed = isLivestreamAllowed;

        var livestreamAllowed = false;

        function identifyUser(user) {
            if (!$window.FS) {
                return;
            }

            var email = user.email;
            $window.FS.identify(email, {
                displayName: email,
                email: email,
            });
        }

        function allowLivestream() {
            if (!$window.FS) {
                return;
            }

            zemFullStoryEndpoint
                .allowLivestream($window.FS.getCurrentSessionURL())
                .then(function() {
                    livestreamAllowed = true;
                });
        }

        function isLivestreamAllowed() {
            return livestreamAllowed;
        }
    });
