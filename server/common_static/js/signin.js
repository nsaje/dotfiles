/*globals $*/

(function () {
    function init() {
        var $usernameInput = $('#id_username');
        var $passwordInput = $('#id_password');
        var $signInBtn = $('#id_signin_btn');
        var $gauthBtn = $('#id_gauth_btn');
        var $signInForm = $('#signin_form');
        var gauthUrl = $('#signin').data('gauth-url');
        var gauthEnabled = !!gauthUrl;

        function getPersonalizedGauthUrl(username) {
            return gauthUrl + '&login_hint=' + encodeURIComponent(username);
        }

        function handleForm() {
            if (gauthEnabled) {
                var username = $usernameInput.val();
                if (username.match(/@zemanta.com$/)) {
                    $passwordInput.hide();
                    $signInBtn.hide();
                    $gauthBtn.show();
                    $gauthBtn.prop('href', getPersonalizedGauthUrl(username));
                } else {
                    $passwordInput.show();
                    $signInBtn.show();
                    $gauthBtn.hide();
                    $gauthBtn.prop('href', gauthUrl);
                }
            }
        }
        
        $signInForm.on('submit', function (e) {
            if (gauthEnabled) {
                var username = $usernameInput.val();
                if (username.match(/@zemanta.com$/)) {
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
