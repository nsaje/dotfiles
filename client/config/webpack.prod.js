var webpack = require('webpack');
var common = require('./webpack.common.js');
var merge = require('webpack-merge');
var AngularCompilerPlugin = require('@ngtools/webpack').AngularCompilerPlugin;
var ForkTsCheckerWebpackPlugin = require('fork-ts-checker-webpack-plugin');
var CopyWebpackPlugin = require('copy-webpack-plugin');
var OptimizeCSSAssetsPlugin = require('optimize-css-assets-webpack-plugin');
var TerserPlugin = require('terser-webpack-plugin');
var HardSourceWebpackPlugin = require('hard-source-webpack-plugin');
var SentryPlugin = require('webpack-sentry-plugin');

var appEnvironment = common.getAppEnvironment();
var configs = [];

if (appEnvironment.buildMainConfig) {
    var mainConfig = generateMainConfig(appEnvironment);
    configs.push(mainConfig);
}

if (appEnvironment.buildStyleConfig) {
    var styleConfig = generateStyleConfig(
        appEnvironment,
        appEnvironment.theme.name
    );
    configs.push(styleConfig);
}

if (appEnvironment.buildWhitelabels) {
    var whitelabels = common.getWhitelabels();
    whitelabels.forEach(function(theme) {
        var styleConfig = generateStyleConfig(appEnvironment, theme.name);
        configs.push(styleConfig);
    });
}

module.exports = configs;

function generateMainConfig(appEnvironment) {
    var config = common.generateMainConfig(appEnvironment);

    if (appEnvironment.aot) {
        config.entry = {
            'zemanta-one': [
                common.root('./one/polyfills.ts'),
                common.root('./one/vendor.ts'),
                common.root('./one/main.aot.ts'),
            ],
        };
    } else {
        config.entry = {
            'zemanta-one': [
                common.root('./one/polyfills.ts'),
                common.root('./one/vendor.ts'),
                common.root('./one/main.jit.ts'),
            ],
        };
    }

    config.output = {
        path: common.root('./dist/one'),
        publicPath: 'one/',
        filename: '[name].js',
        sourceMapFilename: '[file].map',
    };

    config.optimization = {
        minimize: true,
        minimizer: [
            // https://github.com/NMFR/optimize-css-assets-webpack-plugin
            // A Webpack plugin to optimize \ minimize CSS assets.
            new OptimizeCSSAssetsPlugin({}),
            new TerserPlugin({
                sourceMap: true,
                terserOptions: {
                    keep_fnames: true,
                    keep_classnames: true,
                },
            }),
        ],
        splitChunks: {
            cacheGroups: {
                polyfills: {
                    test: /(core-js\/es|core-js\/proposals\/reflect-metadata|zone.js\/dist\/zone)/,
                    chunks: 'all',
                    name: 'zemanta-one.polyfills',
                    priority: 20,
                    enforce: true,
                },
                vendor: {
                    test: /(node_modules|lib\/components)/,
                    chunks: 'all',
                    name: 'zemanta-one.lib',
                    priority: 10,
                    enforce: true,
                },
            },
        },
    };

    // Skip loading styles as they are extracted separately
    config.module.rules.push({
        test: /\.less$/,
        loader: 'null-loader',
    });

    if (appEnvironment.aot) {
        config.module.rules.push({
            test: /(?:\.ngfactory\.js|\.ngstyle\.js|\.tsx?)$/,
            exclude: /node_modules/,
            loader: '@ngtools/webpack',
        });

        config.plugins = config.plugins.concat([
            // https://www.npmjs.com/package/@ngtools/webpack
            // Webpack plugin that AOT compiles Angular components and modules.
            new AngularCompilerPlugin({
                tsConfigPath: common.root('./tsconfig.aot.json'),
                entryModule: common.root('./one/app/app.module.ts#AppModule'),
            }),
        ]);
    } else {
        config.module.rules.push({
            // Angular TypeScript and template loaders
            test: /\.tsx?$/,
            exclude: /node_modules/,
            use: [
                {
                    loader: 'awesome-typescript-loader',
                    options: {
                        transpileOnly: true,
                        configFileName: 'tsconfig.jit.json',
                    },
                },
                {loader: 'angular2-template-loader'},
            ],
        });

        config.plugins = config.plugins.concat([
            // https://github.com/TypeStrong/fork-ts-checker-webpack-plugin
            // Runs typescript type checking in a separate process.
            new ForkTsCheckerWebpackPlugin(),
        ]);
    }

    config.plugins = config.plugins.concat([
        // https://webpack.js.org/plugins/module-concatenation-plugin/
        // Concatenates the scope of all modules into one closure.
        new webpack.optimize.ModuleConcatenationPlugin(),

        // https://webpack.js.org/plugins/copy-webpack-plugin/
        // Copies individual files or entire directories to the build directory.
        new CopyWebpackPlugin({
            patterns: [
                {
                    from: common.root('./one/images'),
                    to: 'images',
                },
                {
                    from: common.root('./one/assets'),
                    to: 'assets',
                },
                {
                    from: common.root('./one/fonts'),
                    to: 'fonts',
                },
            ],
        }),
    ]);

    if (appEnvironment.branchName === 'master') {
        config.plugins = config.plugins.concat([
            // https://github.com/40thieves/webpack-sentry-plugin
            // Webpack plugin to upload source maps to Sentry
            new SentryPlugin({
                release: appEnvironment.buildNumber,
                apiKey: appEnvironment.sentryToken,
                organization: 'zemanta',
                project: 'frontend',
                deleteAfterCompile: true,
                suppressErrors: true,
                filenameTransform: function(filename) {
                    var prefix =
                        '~/build-' +
                        appEnvironment.buildNumber +
                        '/client/one/';
                    return prefix + filename;
                },
            }),
        ]);
    }

    config.devtool = 'source-map';
    config.mode = 'production';

    return config;
}

function generateStyleConfig(appEnvironment, themeName) {
    var mainConfig = common.generateMainConfig(appEnvironment);
    var styleConfig = common.generateStyleConfig(appEnvironment, themeName);

    var config = merge.smart(mainConfig, styleConfig);

    var entryName = 'zemanta-one';
    if (themeName !== appEnvironment.theme.name) {
        entryName = entryName + '-' + themeName;
    }

    config.entry = {};
    config.entry[entryName] = [
        common.root('./one/app/styles/main.less'),
        common.root('./one/main.jit.ts'),
    ];

    config.output = {
        path: common.root('./dist/one'),
        publicPath: 'one/',
    };

    config.optimization = {
        minimize: true,
        minimizer: [
            // https://github.com/NMFR/optimize-css-assets-webpack-plugin
            // A Webpack plugin to optimize \ minimize CSS assets.
            new OptimizeCSSAssetsPlugin({}),
        ],
        splitChunks: {
            cacheGroups: {
                polyfills: {
                    test: /(core-js\/es|core-js\/proposals\/reflect-metadata|zone.js\/dist\/zone)/,
                    chunks: 'all',
                    name: 'zemanta-one.polyfills',
                    priority: 20,
                    enforce: true,
                },
                vendor: {
                    test: /(node_modules|lib\/components)/,
                    chunks: 'all',
                    name: 'zemanta-one.lib',
                    priority: 10,
                    enforce: true,
                },
            },
        },
    };

    config.module.rules.push({
        // Angular TypeScript and template loaders
        test: /\.tsx?$/,
        exclude: /node_modules/,
        use: [
            {
                loader: 'awesome-typescript-loader',
                options: {
                    transpileOnly: true,
                    configFileName: 'tsconfig.jit.json',
                },
            },
            {loader: 'angular2-template-loader'},
        ],
    });

    config.plugins = config.plugins.concat([
        // https://github.com/mzgoddard/hard-source-webpack-plugin
        // Provides an intermediate caching step for modules.
        new HardSourceWebpackPlugin({
            configHash: function() {
                return 'styles-cache';
            },
            environmentHash: {
                files: ['npm-shrinkwrap.json'],
            },
            cachePrune: {
                // Caches younger than `maxAge` are not considered for deletion. They must
                // be at least this (10 min) old in milliseconds.
                maxAge: 10 * 60 * 1000,
                // All caches together must be larger than `sizeThreshold` before any
                // caches will be deleted. Together they must be at least this
                // (500 MB) big in bytes.
                sizeThreshold: 500 * 1024 * 1024,
            },
        }),
        new HardSourceWebpackPlugin.ExcludeModulePlugin([
            {
                test: /mini-css-extract-plugin[\\/]dist[\\/]loader/,
            },
            {
                test: /css-loader/,
            },
            {
                test: /postcss-loader/,
            },
            {
                test: /less-loader/,
            },
        ]),
        new HardSourceWebpackPlugin.SerializerCacachePlugin(),
    ]);

    config.devtool = 'none';
    config.mode = 'production';

    return config;
}
