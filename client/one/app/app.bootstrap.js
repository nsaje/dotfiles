/* globals Raven */
(function () {

    // Initialize app when document is loaded
    // This is standard AngularJS bootstrap hook
    document.onreadystatechange = function () {
        if (document.readyState === 'complete') {
            initialize();
        }
    };

    function initialize () {
        // Raven must be initialized before AngularJS App
        initializeRaven();

        bootstrapApplication();
    }

    function bootstrapApplication () {
        angular.element(function () {
            angular.bootstrap(document, ['one']);
        });
    }

    function initializeRaven () {
        var url = 'https://0005443376e0b054647b8c8759811ad4d5b@sentry.io/147373';
        var options = {
            shouldSendCallback: function () { return !window.zOne.isDebug; }
        };

        Raven.config(url, options)
            .addPlugin(Raven.Plugins.Angular)
            .install();
    }
})();

