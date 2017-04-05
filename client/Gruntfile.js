module.exports = function (grunt) {
    'use strict';

    function getS3BuildPath () {
        if (grunt.option('build-number') !== undefined) {
            return 'https://s3.amazonaws.com/z1-static/build-' + grunt.option('build-number');
        }

        return '';
    }

    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),
        html2js: {
            options: {
                rename: function (moduleName) {
                    return '/' + moduleName;
                }
            },
            one: {
                options: {
                    base: 'one/',
                },
                src: ['one/**/*.html'],
                dest: 'dist/one/zemanta-one.templates.js'
            }
        },
        postcss: {
            options: {
                processors: [
                    require('autoprefixer')({browsers: ['> 1%', 'last 2 versions', 'ie >= 10', 'Firefox ESR']})
                ]
            },
            one: {
                src: 'dist/one/zemanta-one.css'
            }
        },
        concat: {
            one_js: {
                options: {
                    // Replace all 'use strict' statements in the code with a single
                    // one at the top
                    banner: '\'use strict\';\n',
                    process: function (src, filepath) {
                        return '// Source: ' + filepath + '\n' +
                            src.replace(/(^|\n)[ \t]*('use strict'|"use strict");?\s*/g, '$1');
                    }
                },
                src: [
                    'dist/one/zemanta-one.templates.js',
                    'dist/build/config.js',
                    'one/js/constants.js',
                    'one/js/whitelabel.js',
                    // App JS files - start with modules
                    'one/app/app.module.js',
                    'one/app/**/*.module.js',
                    'one/app/**/*.js',
                    // Exclude tests, test helpers and mocks
                    '!one/app/test/**/*',
                    '!one/app/**/*.spec.js',
                    // Legacy app bellow
                    'one/js/app.js',
                    'one/js/constants/*.js',
                    'one/js/services/**/*.js',
                    'one/js/directives/**/*.js',
                    'one/js/services/**/*.js',
                    'one/js/controllers/**/*.js',
                    'one/js/filters/**/*.js',
                    'one/components/**/*.js',
                    '!one/**/*.spec.js',
                ],
                dest: 'dist/one/zemanta-one.js',
            },
            one_styles: {
                src: [
                    'one/app/styles/variables.less',
                    'one/app/styles/mixins.less',
                    'one/app/styles/libExtensions.less',
                    'one/app/styles/utilities.less',
                    'one/app/styles/animations.less',
                    'one/app/styles/base.less',
                    'one/**/*.less',
                    // Exclude dashboard*.less and include it after any other less file in order to make it possible to
                    // override components' styles if needed to make them fit better into dashboard's design
                    // NOTE: dashboard.legacy.less currently exists too and it is included here
                    '!one/app/styles/dashboard*.less',
                    'one/app/styles/dashboard*.less',
                    '!one/app/styles/whitelabel/*.less',
                ],
                dest: 'dist/tmp/zemanta-one.less',
            },
            one_styles_greenpark: {
                src: [
                    'one/app/styles/variables.less',
                    'one/app/styles/whitelabel/greenpark.less',
                    'one/app/styles/mixins.less',
                    'one/app/styles/libExtensions.less',
                    'one/app/styles/utilities.less',
                    'one/app/styles/animations.less',
                    'one/app/styles/base.less',
                    'one/**/*.less',
                    // Exclude dashboard*.less and include it after any other less file in order to make it possible to
                    // override components' styles if needed to make them fit better into dashboard's design
                    // NOTE: dashboard.legacy.less currently exists too and it is included here
                    '!one/app/styles/dashboard*.less',
                    'one/app/styles/dashboard*.less',
                    '!one/app/styles/whitelabel/adtechnacity.less',
                ],
                dest: 'dist/tmp/zemanta-one-greenpark.less',
            },
            one_styles_adtechnacity: {
                src: [
                    'one/app/styles/variables.less',
                    'one/app/styles/whitelabel/adtechnacity.less',
                    'one/app/styles/mixins.less',
                    'one/app/styles/libExtensions.less',
                    'one/app/styles/utilities.less',
                    'one/app/styles/animations.less',
                    'one/app/styles/base.less',
                    'one/**/*.less',
                    // Exclude dashboard*.less and include it after any other less file in order to make it possible to
                    // override components' styles if needed to make them fit better into dashboard's design
                    // NOTE: dashboard.legacy.less currently exists too and it is included here
                    '!one/app/styles/dashboard*.less',
                    'one/app/styles/dashboard*.less',
                    '!one/app/styles/whitelabel/greenpark.less',
                ],
                dest: 'dist/tmp/zemanta-one-adtechnacity.less',
            },
        },
        bower_concat: {
            one_lib: {
                dest: 'dist/one/zemanta-one.lib.js',
                mainFiles: {
                    'highcharts-release': 'highcharts.js',
                    'angular-bootstrap-datetimepicker': 'src/js/datetimepicker.js'
                },
                dependencies: {
                    'angular': 'bootstrap-daterangepicker'
                }
            },
        },
        cssmin: {
            one_styles: {
                files: [{
                    src: 'dist/one/zemanta-one.css',
                    dest: 'dist/one/zemanta-one.min.css',
                }, {
                    src: 'dist/one/zemanta-one-greenpark.css',
                    dest: 'dist/one/zemanta-one-greenpark.min.css',
                }, {
                    src: 'dist/one/zemanta-one-adtechnacity.css',
                    dest: 'dist/one/zemanta-one-adtechnacity.min.css',
                }],
            },
            one_lib: {
                options: {
                    // used to rewrite css urls
                    target: 'lib'
                },
                files: [{
                    src: [
                        'lib/components/bootstrap/dist/css/bootstrap.min.css',
                        'lib/components/angular-bootstrap-datetimepicker/src/css/datetimepicker.css',
                        'lib/components/bootstrap-multiselect/dist/css/bootstrap-multiselect.css',
                        'lib/components/angular-ui-select/dist/select.css',
                        'lib/components/select2/select2.css',
                        'lib/components/select2/select2-bootstrap.css',
                        'lib/components/bootstrap-daterangepicker/daterangepicker.css',
                        'lib/components/ng-tags-input/ng-tags-input.css'
                    ],
                    dest: 'dist/one/zemanta-one.lib.min.css'
                }]
            },
        },
        copy: {
            one: {
                files: [
                    {expand: true, flatten: true, src: 'one/img/*', dest: 'dist/one/img/'},
                    {expand: true, flatten: true, src: 'one/images/*', dest: 'dist/one/images/'},
                    {expand: true, flatten: true, src: 'one/images/whitelabel/greenpark/*',
                     dest: 'dist/one/images/whitelabel/greenpark/'},
                    {expand: true, flatten: true, src: 'one/images/whitelabel/adtechnacity/*',
                     dest: 'dist/one/images/whitelabel/adtechnacity/'},
                    {expand: true, flatten: true, src: 'one/assets/*', dest: 'dist/one/assets/'}
                ]
            },
            // This is used for dev instead of uglifying which takes half of build time
            one_lib: {
                files: [
                    {
                        expand: true,
                        src: [
                            'lib/components/select2/select2.png',
                            'lib/components/select2/select2x2.png',
                            'lib/components/bootstrap/dist/fonts/glyphicons-halflings-regular.woff',
                            'lib/components/bootstrap/dist/fonts/glyphicons-halflings-regular.woff2',
                            'lib/components/bootstrap/dist/fonts/glyphicons-halflings-regular.ttf'
                        ],
                        dest: 'dist/one/'
                    }
                ]
            },
        },
        ngAnnotate: {
            options: {
                singleQuotes: true
            },
            one: {
                files: {
                    'dist/one/zemanta-one.js': ['dist/one/zemanta-one.js']
                }
            }
        },
        uglify: {
            options: {
                sourceMap: true
            },
            one: {
                files: {
                    'dist/one/zemanta-one.min.js': ['dist/one/zemanta-one.js']
                }
            },
            one_lib: {
                files: {
                    'dist/one/zemanta-one.lib.min.js': ['dist/one/zemanta-one.lib.js']
                }
            },
        },
        less: {
            options: {
                rootpath: getS3BuildPath() !== '' ?
                    getS3BuildPath() + '/client/one/' :
                    undefined
            },
            one: {
                files: {
                    'dist/one/zemanta-one.css': 'dist/tmp/zemanta-one.less',
                    'dist/one/zemanta-one-greenpark.css': 'dist/tmp/zemanta-one-greenpark.less',
                    'dist/one/zemanta-one-adtechnacity.css': 'dist/tmp/zemanta-one-adtechnacity.less',
                }
            },
        },
        watch: {
            options: {
                livereload: true
            },
            one_js: {
                files: [
                    'one/**/*.js',
                    '!one/test/**/*',
                    '!one/**/*.spec.js',
                ],
                tasks: ['concat:one_js', 'ngAnnotate:one', 'clean:tmp']
            },
            one_styles: {
                files: [
                    'one/**/*.less',
                ],
                tasks: ['concat:one_styles',
                        'concat:one_styles_greenpark', 'concat:one_styles_adtechnacity',
                        'less:one', 'postcss:one', 'clean:tmp']
            },
            one_templates: {
                files: [
                    'one/**/*.html',
                    'one/img/**/*',
                    'one/images/**/*',
                    'one/assets/**/*',
                ],
                tasks: ['build:one']
            },
        },
        connect: {
            dev: {
                options: {
                    port: 9999,
                    base: 'dist/',
                    directory: 'dist/',
                    hostname: '*',
                    debug: true,
                    livereload: true,
                    protocol: 'http',
                    middleware: function (connect, options) {
                        return [
                            function (req, res, next) {

                                res.setHeader('Access-Control-Allow-Origin', '*');
                                return next();
                            },
                            connect.static(require('path').resolve('dist/'))
                        ];
                    }
                }
            }
        },
        ngconstant: {
            options: {
                name: 'config',
                dest: 'dist/build/config.js'
            },
            prod: {
                constants: {
                    config: {
                        static_url: getS3BuildPath() + '/client',
                        debug: false
                    }
                }
            },
            dev: {
                constants: {
                    config: {
                        static_url: 'http://localhost:9999',
                        debug: true
                    }
                }
            }
        },
        karma: {
            local: {
                configFile: 'karma.conf.js',
                singleRun: true,
            },
        },
        jslint: { // configure the task
            // lint your project's server code
            server: {
                src: [
                    'dist/one/zemanta-one.templates.js',
                    'dist/build/config.js',
                    'one/js/constants.js',
                    'one/js/whitelabel.js',
                    'one/js/app.js',
                    'one/js/constants/*.js',
                    'one/js/services/**/*.js',
                    'one/js/directives/**/*.js',
                    'one/js/services/**/*.js',
                    'one/js/controllers/**/*.js',
                    'one/js/filters/**/*.js',
                    'one/components/**/*.js',
                ],
                exclude: [],
                directives: { // example directives
                    node: true,
                    todo: true,
                },
                options: {
                    edition: 'latest', // specify an edition of jslint or use 'dir/mycustom-jslint.js' for own path
                    junit: 'out/server-junit.xml', // write the output to a JUnit XML
                    log: 'out/server-lint.log',
                    jslintXml: 'out/server-jslint.xml',
                    errorsOnly: true, // only display errors
                    failOnError: true, // defaults to true
                    checkstyle: 'out/server-checkstyle.xml' // write a checkstyle-XML
                }
            }
        },
        clean: {
            // Remove dist/tmp directory containing temporary files used by different steps in build process
            tmp: ['dist/tmp'],
        },
        build: {
            one: ['html2js:one', 'concat:one_js', 'ngAnnotate:one', 'concat:one_styles',
                  'concat:one_styles_greenpark', 'concat:one_styles_adtechnacity',
                  'less:one', 'postcss:one', 'copy:one', 'clean:tmp'],

            one_lib: ['bower_concat:one_lib', 'cssmin:one_lib', 'copy:one_lib'],
        },
        dist: {
            one: ['uglify:one', 'cssmin:one_styles'],
            one_lib: ['uglify:one_lib'],
        },
    });

    require('load-grunt-tasks')(grunt, {scope: 'devDependencies'});

    grunt.registerMultiTask('build', 'Build project.', function () {
        grunt.task.run(this.data);
    });
    grunt.registerMultiTask('dist', 'Prepare distribution bundle.', function () {
        grunt.task.run(this.data);
    });

    grunt.registerTask('default', ['ngconstant:prod', 'build', 'dist']);
    grunt.registerTask('prod', ['default', 'karma:local']);
    grunt.registerTask('test', ['build', 'karma:local']);
    grunt.registerTask('dev', ['ngconstant:dev', 'build', 'connect:dev', 'watch']);
    grunt.registerTask('lint', ['ngconstant:dev', 'jslint']);
};
