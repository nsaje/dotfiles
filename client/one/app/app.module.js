angular.module(
    'one',
    [
        'one.libs', // NOTE: Must be referenced first!
        'one.core',
        'one.common',
        'one.services',
        'one.views',
        'one.widgets',
    ]
);

angular.module('one').config(function ($compileProvider, config) {
    $compileProvider.debugInfoEnabled(config.debug);
});

angular.module('one').config(function ($sceDelegateProvider, config) {
    $sceDelegateProvider.resourceUrlWhitelist(['self', config.static_url + '/**']);
});

angular.module('one').config(function ($httpProvider) {
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
});

angular.module('one').config(function ($locationProvider) {
    $locationProvider.html5Mode(true);
    $locationProvider.hashPrefix('!');
});

angular.module('one').config(function (uibDatepickerConfig, uibDatepickerPopupConfig) { // eslint-disable-line max-len
    uibDatepickerConfig.showWeeks = false;
    uibDatepickerConfig.formatDayHeader = 'EEE';
    uibDatepickerPopupConfig.showButtonBar = false;
});

angular.module('one').config(function ($uibTooltipProvider) {
    $uibTooltipProvider.setTriggers({'openTutorial': 'closeTutorial'});
});

// HACK: Update ui-select2 directive priority after initialization. There's a bug in deprecated angular-ui-select2
// library caused by library's incompatibility with Angular >= 1.5 that prevents ng-model changes to be reflected in
// ui-select2 directive.
angular.module('one').config(function ($provide) {
    $provide.decorator('uiSelect2Directive', function ($delegate) {
        var directive;
        directive = $delegate[0];
        directive.priority = 10;
        return $delegate;
    });
});

var locationSearch;
// Fixes https://github.com/angular-ui/ui-router/issues/679
angular.module('one').run(function ($state, $rootScope, $location, config, zemIntercomService) {  // eslint-disable-line max-len
    $rootScope.config = config;
    $rootScope.$state = $state;

    // [WORKAROUND] Wrap state change event into custom one and use in app
    // This enables us to navigate to states without reinitialization (notify: false) but
    // still using state change events to refresh depended services and components
    $rootScope.$on('$stateChangeStart', function () {
        $rootScope.$broadcast('$zemStateChangeStart');
    });
    $rootScope.$on('$stateChangeSuccess', function () {
        $rootScope.$broadcast('$zemStateChangeSuccess');
    });
    // [END WORKAROUND]

    $rootScope.$on('$zemStateChangeStart', function () {
        // Save location.search so we can add it back after transition is done
        if (!locationSearch) locationSearch = $location.search();
    });

    $rootScope.$on('$zemStateChangeSuccess', function () {
        // Restore all query string parameters back to $location.search
        // and keep the new ones if applied in the process of changing state
        // (e.g. params passed through ui-router $state)
        angular.merge(locationSearch, $location.search());
        $location.search(locationSearch);
        locationSearch = null;
    });

    $rootScope.$on('$locationChangeSuccess', function () {
        zemIntercomService.update();
    });

    $rootScope.tabClick = function (event) {
        // Function to fix opening tabs in new tab when clicking with the middle button
        // This is effectively a workaround for a bug in bootstrap-ui
        if (event.which === 2 || (event.which === 1 && (event.metaKey || event.ctrlKey))) {
           // MIDDLE CLICK or CMD+LEFTCLICK
           // the regular link will open in new tab if we stop the event propagation
            event.stopPropagation();
        }
    };
});


angular.module('one').run(function (zemInitializationService) {
    zemInitializationService.initApp();
});
