(function () {
    function init() {
        var $usernameInput = $('#id_username');
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

            // exclude alias emails, e.g. name+alias@outbrain.com
            return email.match(/^([^\+]+)(@zemanta.com|@outbrain.com)$/i);
        }

        function handleForm() {
            if (gauthEnabled) {
                var username = $usernameInput.val();
                if (isGauthEmail(username)) {
                    $('#id_password').hide();
                    $signInBtn.val('Sign In With Google');
                } else {
                    $('#id_password').show();
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

        $usernameInput.keyup(function (e) {
            handleForm();
        });

        $usernameInput.on('input', function (e) {
            handleForm();
        });

        handleForm();

        $usernameInput.placeholder();
        $('#id_password').placeholder();
    }

    $(document).ready(function (e) {
        init();
    });
}());
