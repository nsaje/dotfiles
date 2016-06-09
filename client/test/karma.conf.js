// Karma configuration
// Generated on Tue Jul 01 2014 10:34:40 GMT+0200 (CEST)

module.exports = function (config) {
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
        'one/js/**/*.js',
        'one/components/**/*.js',
        'actionlog/**/*.js',
        'test/unit/**/*.js'
    ],

      preprocessors: {
        '{actionlog,one}/js/**/*.js': 'coverage'
    },


    // test results reporter to use
    // possible values: 'dots', 'progress'
    // available reporters: https://npmjs.org/browse/keyword/karma-reporter
      reporters: ['progress', 'coverage', 'junit'],


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
      browsers: ['Chrome'],


    // Continuous Integration mode
    // if true, Karma captures browsers, runs the tests and exits
      singleRun: false,

      coverageReporter: {
        reporters: [
            {
                type: 'text-summary',
                dir: 'coverage/text/',
                file: 'coverage.txt',
            },
            {
                type: 'html',
                dir: 'coverage/html',
            },
            {
                type: 'cobertura',
                dir: 'coverage/cobertura',
                file: 'cobertura.xml',
            },
            {
                type: 'lcov',
                dir: 'coverage/lcov',
            },
        ],
    },


      plugins: [
        'karma-jasmine',
        'karma-chrome-launcher',
        'karma-coverage',
        'karma-junit-reporter',
    ],
  });
};
