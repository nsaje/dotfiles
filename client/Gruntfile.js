module.exports = function (grunt) {
    'use strict';

    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),
        html2js: {
            options: {
                base: 'app/',
                rename: function (moduleName) {
                    return '/' + moduleName;
                }
            },
            dist: {
                src: ['app/partials/**.html'],
                dest: 'app/dist/js/zemanta-one.templates.js'
            }
        },
        concat: {
            dist: {
                options: {
                    // Replace all 'use strict' statements in the code with a single
                    // one at the top
                    banner: "'use strict';\n",
                    process: function(src, filepath) {
                        return '// Source: ' + filepath + '\n' +
                            src.replace(/(^|\n)[ \t]*('use strict'|"use strict");?\s*/g, '$1');
                    }
                },
                src: [
                    'app/js/config.js',
                    'app/js/constants.js',
                    'app/js/app.js',
                    'app/js/app_actionlog.js',
                    'app/js/services/**/*.js',
                    'app/js/directives/**/*.js',
                    'app/js/services/**/*.js',
                    'app/js/controllers/**/*.js',
                    'app/js/filters/**/*.js',
                    'app/dist/js/zemanta-one.templates.js'
                ],
                dest: 'app/dist/js/zemanta-one.js'
            }
        },
        uglify: {
            dist: {
                options: {
                    sourceMap: true
                },
                files: {
                    'app/dist/js/zemanta-one.min.js': ['app/dist/js/zemanta-one.js']
                }
            }
        },
        less: {
            dist: {
                options: {
                    cleancss: true
                },
                files: {
                    "app/dist/css/zemanta-one.min.css": "app/less/**/*.less"
                }
            }
        },
        watch: {
            'dist-js': {
                options: {
                    livereload: true
                },
                files: [
                    'app/js/**/*.js'
                ],
                tasks: ['dist-js']
            },
            'dist-less': {
                options: {
                    livereload: true
                },
                files: [
                    'app/less/**/*.less'
                ],
                tasks: ['dist-less']
            }
        },
        clean: {
            dist: ['app/dist']
        },
        connect: {
            dev: {
                options: {
                    port: 9999,
                    base: 'app/',
                    directory: 'app/',
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
                            connect.static(require('path').resolve('app/'))
                        ];
                    }
                }
            }
        },
        ngconstant: {
            options: {
                name: 'config',
                dest: 'app/js/config.js',
                constants: {
                    config: {
                        static_url: '/client'    
                    }
                }
            },
            prod: {},
            dev: {
                constants: {
                    config: {
                        static_url: 'http://localhost:9999'
                    }
                }    
            }
        },
        karma: {
            local: {
                configFile: 'test/karma.conf.js',
                singleRun: true,
            },
            sauce: {
                configFile: 'test/karma.conf-sauce.js'
            }
        },
        protractor: {
            local: {
                configFile: 'test/protractor.conf.js',
                chromeDriver: 'node_modules/grunt-protractor-runner/node_modules/protractor/bin/webdriver-manager update',
            },
            sauce: {
                configFile: 'test/protractor.conf-sauce.js'
            }
        }
    });

    require('load-grunt-tasks')(grunt, {scope: 'devDependencies'});

    grunt.registerTask('dist-js', ['html2js', 'concat:dist', 'uglify:dist']);
    grunt.registerTask('dist-less', ['less:dist']);
    grunt.registerTask('build', ['dist-js', 'dist-less'])
    grunt.registerTask('default', ['ngconstant:prod', 'build']);
    grunt.registerTask('test', ['default', 'karma:' + (grunt.option('sauce') ? 'sauce' : 'local')]);
    grunt.registerTask('e2e', ['protractor:' + (grunt.option('sauce') ? 'sauce' : 'local')]);
    grunt.registerTask('dev', ['ngconstant:dev', 'build', 'connect:dev', 'watch']);
};
