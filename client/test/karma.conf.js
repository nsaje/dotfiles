// Karma configuration
// Generated on Tue Jul 01 2014 10:34:40 GMT+0200 (CEST)

module.exports = function(config) {
  config.set({

    // base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: '..',


    // frameworks to use
    // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
    frameworks: ['jasmine'],


    // list of files / patterns to load in the browser
    files: [
        'app/lib/components/jquery/dist/jquery.min.js',
        'app/lib/components/angular/angular.js',
        'app/lib/components/moment/min/moment.min.js',
        'app/lib/ng-bs-daterangepicker/0.0.1/ng-bs-daterangepicker.js',
        'app/lib/components/angular-ui-router/release/angular-ui-router.min.js',
        'app/lib/components/angular-bootstrap/ui-bootstrap-tpls.min.js',
        'app/lib/components/angular-bootstrap-datetimepicker/src/js/datetimepicker.js',
        'app/lib/components/angular-ui-select2/src/select2.js',
        'app/lib/components/highcharts-ng/dist/highcharts-ng.min.js',
        'app/lib/components/angular-sanitize/angular-sanitize.min.js',
        'app/lib/components/angular-local-storage/angular-local-storage.min.js',
        'app/lib/components/angular-mocks/angular-mocks.js',
        'app/js/**/*.js',
        'test/unit/**/*.js'
    ],


    // test results reporter to use
    // possible values: 'dots', 'progress'
    // available reporters: https://npmjs.org/browse/keyword/karma-reporter
    reporters: ['progress'],


    // web server port
    port: 9876,


    // enable / disable colors in the output (reporters and logs)
    colors: true,


    // level of logging
    // possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
    logLevel: config.LOG_INFO,


    // enable / disable watching file and executing tests whenever any file changes
    autoWatch: true,


    // start these browsers
    // available browser launchers: https://npmjs.org/browse/keyword/karma-launcher
    browsers: ['Chrome', 'Firefox'],


    // Continuous Integration mode
    // if true, Karma captures browsers, runs the tests and exits
    singleRun: false,


    plugins: [
        'karma-jasmine',
        'karma-chrome-launcher',
        'karma-firefox-launcher',
    ]
  });
};
