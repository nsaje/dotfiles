module.exports = function (grunt) {
    'use strict';

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
                src: ['one/partials/**/*.html'],
                dest: 'dist/one/zemanta-one.templates.js'
            }
        },
        concat: {
            options: {
                // Replace all 'use strict' statements in the code with a single
                // one at the top
                banner: "'use strict';\n",
                process: function(src, filepath) {
                    return '// Source: ' + filepath + '\n' +
                        src.replace(/(^|\n)[ \t]*('use strict'|"use strict");?\s*/g, '$1');
                }
            },
            one: {
                src: [
                    'dist/one/zemanta-one.templates.js',
                    'dist/build/config.js',
                    'one/js/constants.js',
                    'one/js/app.js',
                    'one/js/constants/*.js',
                    'one/js/services/**/*.js',
                    'one/js/directives/**/*.js',
                    'one/js/services/**/*.js',
                    'one/js/controllers/**/*.js',
                    'one/js/filters/**/*.js',
                    'one/js/demo.js'
                ],
                dest: 'dist/one/zemanta-one.js'
            },
            actionlog: {
                src: [
                    'dist/build/config.js',
                    'actionlog/app.js',
                    'actionlog/js/**/*.js'
                ],
                dest: 'dist/actionlog/zemanta-one.actionlog.js'
            }
        },
        bower_concat: {
            one_lib: {
                dest: 'dist/one/zemanta-one.lib.js',
                mainFiles: {
                    'highcharts-release': 'highcharts.js'
                },
                dependencies: {
                    'angular': 'bootstrap-daterangepicker'
                }
            },
            actionlog_lib: {
                dest: 'dist/actionlog/zemanta-one.actionlog.lib.js',
                cssDest: 'dist/actionlog/zemanta-one.actionlog.lib.css',
                include: [
                    'jquery',
                    'bootstrap',
                    'angular',
                    'angular-bootstrap',
                ]
            }
        },
        cssmin: {
            options: {
                // used to rewrite css urls
                target: 'lib'
            },
            one_lib: {
                files: [{
                    src: [
                        'lib/components/bootstrap/dist/css/bootstrap.min.css',
                        'lib/components/angular-bootstrap-datetimepicker/src/css/datetimepicker.css',
                        'lib/components/bootstrap-multiselect/css/bootstrap-multiselect.css',
                        'lib/components/angular-ui-select/dist/select.css',
                        'lib/components/select2/select2.css',
                        'lib/components/select2/select2-bootstrap.css',
                        'lib/components/bootstrap-daterangepicker/daterangepicker-bs3.css'
                    ],
                    dest: 'dist/one/zemanta-one.lib.min.css'
                }]
            },
            actionlog_lib: {
                files: [{
                    src: 'dist/actionlog/zemanta-one.actionlog.lib.css',
                    dest: 'dist/actionlog/zemanta-one.actionlog.lib.min.css'
                }]
            }
        },
        copy: {
            one: {
                files: [
                    {expand: true, flatten: true, src: 'one/img/*', dest: 'dist/one/img/'},
                    {expand: true, flatten: true, src: 'one/assets/*', dest: 'dist/one/assets/'}
                ]
            },
            // This is used for dev instead of uglifying which takes half of build time
            onedev: {
                files: [
                        {src: 'dist/one/zemanta-one.js', dest: 'dist/one/zemanta-one.min.js'},
                    ]
            },
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
            actionlog: {
                files: [
                    {expand: true, flatten: true, src: 'actionlog/partials/**/*.html', dest: 'dist/actionlog/'},
                    {expand: true, flatten: true, src: 'actionlog/img/*', dest: 'dist/actionlog/img/'}
                ]
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
            actionlog: {
                files: {
                    'dist/actionlog/zemanta-one.actionlog.min.js': ['dist/actionlog/zemanta-one.actionlog.js']
                }
            },
            actionlog_lib: {
                files: {
                    'dist/actionlog/zemanta-one.actionlog.lib.min.js': ['dist/actionlog/zemanta-one.actionlog.lib.js']
                }
            }
        },
        less: {
            options: {
                cleancss: true,
                rootpath: grunt.option('build-number') !== undefined ?
                    "https://s3.amazonaws.com/z1-static/build-" + grunt.option('build-number') + "/client/one/" :
                    undefined
            },
            one: {
                files: {
                    "dist/one/zemanta-one.min.css": "one/less/**/*.less"
                }
            },
            actionlog: {
                files: {
                    "dist/actionlog/zemanta-one.actionlog.min.css": "actionlog/less/**/*.less"
                }
            }
        },
        watch: {
            options: {
                livereload: true
            },
            one: {
                files: [
                    'one/js/**/*.js',
                    'one/partials/**/*.html',
                    'one/img/**/*'
                ],
                tasks: ['html2js:one', 'concat:one', 'copy:onedev', 'copy:one']
            },
            one_css: {
                files: [
                    'one/less/**/*.less',
                ],
                tasks: ['less:one', 'copy:one']
            },
            actionlog: {
                files: [
                    'actionlog/**/*.js',
                    'actionlog/partials/**/*.html',
                    'actionlog/less/**/*.less',
                    'actionlog/img/**/*'
                ],
                tasks: ['build:actionlog']
            }
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
                        static_url: "https://s3.amazonaws.com/z1-static/build-" + grunt.option('build-number') + "/client",
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
                configFile: 'test/karma.conf.js',
                singleRun: true
            },
            sauce: {
                configFile: 'test/karma.conf-sauce.js'
            }
        },
        protractor: {
            local: {
                configFile: 'test/protractor.conf.js',
                chromeDriver: 'node_modules/grunt-protractor-runner/node_modules/protractor/bin/webdriver-manager update'
            },
            sauce: {
                configFile: 'test/protractor.conf-sauce.js'
            }
        },
        build: {
            one: ['html2js:one', 'concat:one', 'uglify:one', 'less:one', 'copy:one'],
            one_lib: ['bower_concat:one_lib', 'uglify:one_lib', 'cssmin:one_lib', 'copy:one_lib'],
            actionlog: ['concat:actionlog', 'uglify:actionlog', 'less:actionlog', 'copy:actionlog'],
            actionlog_lib: ['bower_concat:actionlog_lib', 'uglify:actionlog_lib', 'cssmin:actionlog_lib']
        }
    });

    require('load-grunt-tasks')(grunt, {scope: 'devDependencies'});

    grunt.registerMultiTask('build', 'Build project.', function () {
        grunt.task.run(this.data);
    });

    grunt.registerTask('default', ['ngconstant:prod', 'build']);
    grunt.registerTask('test', ['default', 'karma:' + (grunt.option('sauce') ? 'sauce' : 'local')]);
    grunt.registerTask('e2e', ['protractor:' + (grunt.option('sauce') ? 'sauce' : 'local')]);
    grunt.registerTask('dev', ['ngconstant:dev', 'build', 'connect:dev', 'watch']);
};
