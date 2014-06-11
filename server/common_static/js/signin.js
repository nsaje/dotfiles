/*globals $*/

(function () {
    function init() {
        var $usernameInput = $('#id_username');
        var $passwordInput = $('#id_password');
        var $signInBtn = $('#id_signin_btn');
        var $signInForm = $('#signin_form');
        var gauthUrl = $('#signin').data('gauth-url');
        var gauthEnabled = !!gauthUrl;

        function getPersonalizedGauthUrl(username) {
            return gauthUrl + '&login_hint=' + encodeURIComponent(username);
        }

        function isGauthEmail(email) {
            if (!email) {
                return false;
            }

            return email.match(/@zemanta.com$/);
        }

        function handleForm() {
            if (gauthEnabled) {
                var username = $usernameInput.val();
                if (isGauthEmail(username)) {
                    $passwordInput.hide();
                    $signInBtn.val('Sign In With Google');
                } else {
                    $passwordInput.show();
                    $signInBtn.val('Sign In');
                }
            }
        }
        
        $signInForm.on('submit', function (e) {
            if (gauthEnabled) {
                var username = $usernameInput.val();
                if (isGauthEmail(username)) {
                    e.preventDefault();
                    window.location.href = getPersonalizedGauthUrl(username);
                }
            }
        });

        $usernameInput.on('input', function (e) {
            handleForm();
        });

        handleForm();
    }

    $(document).ready(function (e) {
        init();
    });
}());
