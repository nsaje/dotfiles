var fs = require('fs');
var path = require('path');

module.exports = function (config) {

    if (!process.env.SAUCE_USERNAME) {
        if (!fs.existsSync(path.join(__dirname, 'sauce.json'))) {
            console.log('Create a sauce.json with your credentials based on the sauce.json.template file.');
            process.exit(1);
        } else {
            process.env.SAUCE_USERNAME = require('./sauce').username;
            process.env.SAUCE_ACCESS_KEY = require('./sauce').accessKey;
        }
    }

    var customLaunchers = {
        sl_chrome: {
            base: 'SauceLabs',
            browserName: 'chrome',
            platform: 'Windows 7',
            version: '35'
        },
        sl_firefox: {
            base: 'SauceLabs',
            browserName: 'firefox',
            version: '30'
        },
        sl_safari_6: {
            base: 'SauceLabs',
            browserName: 'safari',
            platform: 'OS X 10.8',
            version: '6'
        },
        sl_safari_7: {
            base: 'SauceLabs',
            browserName: 'safari',
            platform: 'OS X 10.9',
            version: '7'
        },
        sl_ie_11: {
            base: 'SauceLabs',
            browserName: 'internet explorer',
            platform: 'Windows 8.1',
            version: '11'
        },
        sl_ie_10: {
            base: 'SauceLabs',
            browserName: 'internet explorer',
            platform: 'Windows 7',
            version: '10'
        },
        sl_ie_9: {
            base: 'SauceLabs',
            browserName: 'internet explorer',
            platform: 'Windows 7',
            version: '9'
        },
    };

    config.set({
        // base path that will be used to resolve all patterns (eg. files, exclude)
        basePath: '..',


        // frameworks to use
        // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
        frameworks: ['jasmine'],


        // list of files / patterns to load in the browser
        files: [
            'dist/one/zemanta-one.lib.js',
            'dist/one/zemanta-one.templates.js',
            'dist/actionlog/zemanta-one.actionlog.lib.js',
            'one/js/**/*.js',
            'actionlog/**/*.js',
            'test/unit/**/*.js'
        ],



        // test results reporter to use
        // possible values: 'dots', 'progress'
        // available reporters: https://npmjs.org/browse/keyword/karma-reporter
        reporters: ['progress', 'saucelabs'],


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
        browsers: Object.keys(customLaunchers),


        // Continuous Integration mode
        // if true, Karma captures browsers, runs the tests and exits
        singleRun: true,

        captureTimeout: 300000,

        browserNoActivityTimeout: 60000,

        sauceLabs: {
            testName: 'Zemanta One Client'
        },

        customLaunchers: customLaunchers
    });
};
