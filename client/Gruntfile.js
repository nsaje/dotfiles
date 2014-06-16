module.exports = function (grunt) {
    'use strict';

    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),
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
                    'app/js/*.js',
                    'app/js/directives/**/*.js',
                    'app/js/controllers/**/*.js'
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
        }
    });

    require('load-grunt-tasks')(grunt, {scope: 'devDependencies'});

    grunt.registerTask('dist-js', ['concat:dist', 'uglify:dist']);
    grunt.registerTask('dist-less', ['less:dist']);
    grunt.registerTask('default', ['dist-js', 'dist-less']);
    grunt.registerTask('dev', ['default', 'connect:dev', 'watch']);
};
