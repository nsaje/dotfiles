// Karma configuration
// Generated on Tue Jul 01 2014 10:34:40 GMT+0200 (CEST)
// Reference: http://karma-runner.github.io/0.12/config/configuration-file.html
module.exports = function karmaConfig (config) {
    config.set({
        frameworks: [
            // Reference: https://github.com/karma-runner/karma-jasmine
            // Set framework to jasmine
            'jasmine',
        ],

        reporters: [
            // Reference: https://github.com/mlex/karma-spec-reporter
            // Set reporter to print detailed results to console
            'spec',

            // Output test results in JUnit XML format
            'junit',
        ],

        specReporter: {
            suppressErrorSummary: true, // Do not print error summary
            suppressFailed: false,      // Print information about failed tests
            suppressPassed: true,       // Do not print information about passed tests
            suppressSkipped: true,      // Do not print information about skipped tests
            showSpecTiming: false,      // Do not print the time elapsed for each spec
            failFast: false,            // Test won't finish with error when a first fail occurs
        },

        junitReporter: {
            useBrowserName: false,
            outputFile: './test-results.xml',
        },

        files: [
            {pattern: './one/tests.ts', watched: false},
        ],

        exclude: [],

        preprocessors: {
            './one/tests.ts': ['webpack', 'sourcemap'],
        },

        browsers: [
            // Run tests using PhantomJS
            'PhantomJS',
        ],

        singleRun: true,

        webpack: require('./webpack.config'),

        // Hide webpack build information from output
        webpackMiddleware: {
            noInfo: 'errors-only',
        },
    });
};
