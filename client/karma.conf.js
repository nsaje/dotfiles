// Karma configuration
// Generated on Tue Jul 01 2014 10:34:40 GMT+0200 (CEST)
// Reference: http://karma-runner.github.io/0.12/config/configuration-file.html
module.exports = function karmaConfig (config) {
    config.set({
        frameworks: [
            // Reference: https://github.com/karma-runner/karma-jasmine
            // Set framework to jasmine
            'jasmine'
        ],

        reporters: [
            // Reference: https://github.com/mlex/karma-spec-reporter
            // Set reporter to print detailed results to console
            'progress',

            // Output test results in JUnit XML format
            'junit'
        ],

        junitReporter: {
            useBrowserName: false,
            outputFile: './test-results.xml'
        },

        files: [
            // Grab all files in the app folder that contain .spec.
            'one/tests.webpack.js'
        ],

        preprocessors: {
            // Reference: http://webpack.github.io/docs/testing.html
            // Reference: https://github.com/webpack/karma-webpack
            // Convert files with webpack and load sourcemaps
            'one/tests.webpack.js': ['webpack', 'sourcemap']
        },

        browsers: [
            // Run tests using PhantomJS
            'PhantomJS'
        ],

        singleRun: true,

        webpack: require('./webpack.config'),

        // Hide webpack build information from output
        webpackMiddleware: {
            noInfo: 'errors-only'
        },
    });
};
