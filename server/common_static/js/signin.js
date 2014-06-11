/*globals $*/

(function () {
    function init() {
        var $usernameInput = $('#id_username');
        var $passwordInput = $('#id_password');
        var $signInBtn = $('#id_signin_btn');
        var $gauthBtn = $('#id_gauth_btn');

        function handleForm() {
            if ($gauthBtn) {
                if ($usernameInput.val().match(/@zemanta.com$/)) {
                    $passwordInput.hide();
                    $signInBtn.hide();
                    $gauthBtn.show();
                } else {
                    $passwordInput.show();
                    $gauthBtn.hide();
                    $signInBtn.show();
                }
            }
        }

        $usernameInput.on('input', function (e) {
            handleForm();
        });

        handleForm();
    }

    $(document).ready(function (e) {
        init();
    });
}());
