var webpack = require('webpack');
var path = require('path');
var MiniCssExtractPlugin = require('mini-css-extract-plugin');
var FilterChunkWebpackPlugin = require('filter-chunk-webpack-plugin');

var APP_CONFIG = null;
var THEMES = {
    one: {name: 'one'},
    adtechnacity: {name: 'adtechnacity'},
    greenpark: {name: 'greenpark'},
    newscorp: {name: 'newscorp'},
    burda: {name: 'burda'},
    mediamond: {name: 'mediamond'},
};

module.exports.THEMES = THEMES;
module.exports.getAppConfig = getAppConfig;
module.exports.getTheme = getTheme;
module.exports.getThemes = getThemes;
module.exports.generateMainConfig = generateMainConfig;
module.exports.generateStyleConfig = generateStyleConfig;
module.exports.root = root;

function getAppConfig() {
    if (!APP_CONFIG) {
        APP_CONFIG = generateAppConfig(process.env);
    }
    return APP_CONFIG;
}

function getTheme(name) {
    return THEMES[name] || THEMES.one;
}

function getThemes() {
    return THEMES;
}

function generateMainConfig(appConfig) {
    var config = {
        module: {},
        plugins: [],
    };

    config.resolve = {
        extensions: ['.ts', '.js'],
        modules: [root('./one'), 'node_modules'],
        alias: {
            angular: root('./lib/components/angular/angular.js'),
            jquery: root('./lib/components/jquery/dist/jquery.js'),
            moment: root('./lib/components/moment/moment.js'),
        },
    };

    config.module.rules = [
        {
            // Webpack loader to annotate angular applications. Generates a sourcemaps as well.
            test: /\.js$/,
            include: [root('./one/app/ajs-app')],
            use: [{loader: 'ng-annotate-loader'}],
        },
        {
            // Angular TypeScript and template loaders
            test: /\.tsx?$/,
            loaders: ['awesome-typescript-loader', 'angular2-template-loader'],
        },
        {
            // https://github.com/angular/universal-starter/pull/593/commits/644c5f6f28a760f94ef111f5a611e2c9ed679b6a
            // Mark files inside `@angular/core` as using SystemJS style dynamic imports.
            // Removing this will cause deprecation warnings to appear.
            test: /(\\|\/)@angular(\\|\/)core(\\|\/).+\.js$/,
            parser: {system: true},
        },
        {
            // Allow loading html through js
            test: /\.html$/,
            loader: 'html-loader',
        },
        {
            test: /\.css$/,
            use: [
                {loader: MiniCssExtractPlugin.loader},
                {loader: 'css-loader'},
            ],
        },
        {
            test: /\.(png|jpg|jpeg|gif|svg|woff|woff2|ttf|eot)$/,
            loader: 'url-loader',
        },
        {
            // Workaround: Convert AngularJS to CommonJS module
            test: /angular\.js$/,
            loader: 'exports-loader?angular',
            include: [root('./lib/components/angular')],
        },
    ];

    config.plugins = [
        // Workaround for angular/angular#11580
        new webpack.ContextReplacementPlugin(
            // The (\\|\/) piece accounts for path separators in *nix and Windows
            /@angular(\\|\/)core(\\|\/)fesm5/,
            root('./one'), // location of your src
            {} // a map of your routes
        ),

        // https://github.com/webpack-contrib/mini-css-extract-plugin
        // This plugin extracts CSS into separate files.
        new MiniCssExtractPlugin({
            filename: '[name].css',
        }),

        // https://webpack.js.org/plugins/define-plugin/
        // Allows you to create global constants which can be configured at compile time.
        // Define application configuration.
        new webpack.DefinePlugin({APP_CONFIG: JSON.stringify(appConfig)}),

        // Fix issue with moment.js locales - by default all locales are added (~30k loc)
        new webpack.ContextReplacementPlugin(/moment[/\\]locale$/, /en/),

        // https://webpack.js.org/plugins/provide-plugin/
        // Automatically load modules instead of having to import or require them everywhere.
        new webpack.ProvidePlugin({
            $: 'jquery',
            jQuery: 'jquery',
            'window.jQuery': 'jquery',
            moment: 'moment',
        }),
    ];

    return config;
}

function generateStyleConfig(themeName) {
    var config = {
        module: {},
        plugins: [],
    };

    config.module.rules = [
        {
            test: /\.less$/,
            use: [
                {loader: MiniCssExtractPlugin.loader},
                {
                    loader: 'css-loader',
                    options: {
                        url: false,
                    },
                },
                {
                    loader: 'postcss-loader',
                    options: {
                        plugins: [require('autoprefixer')()],
                    },
                },
                {
                    loader: 'less-loader',
                    options: {
                        paths: [root('./one/app/themes/' + themeName)],
                        relativeUrls: false,
                        rootpath: APP_CONFIG.staticUrl + '/one/',
                    },
                },
            ],
        },
    ];

    config.plugins = [
        // https://github.com/webpack-contrib/mini-css-extract-plugin
        // This plugin extracts CSS into separate files.
        new MiniCssExtractPlugin({
            filename: '[name].css',
        }),

        // https://www.npmjs.com/package/filter-chunk-webpack-plugin
        // Include or exclude files / chunks from the final webpack output based on a list of patterns.
        new FilterChunkWebpackPlugin({
            patterns: ['*.js'],
        }),
    ];

    return config;
}

function generateAppConfig(env) {
    var config = {
        env: {
            dev: env.NODE_ENV === 'development' || !env.NODE_ENV,
            test: env.NODE_ENV === 'test',
            prod: env.NODE_ENV === 'production',
        },
        buildNumber: env.npm_config_build_number || '',
        branchName: env.npm_config_branch_name || '',
        theme: env.npm_config_theme || '',
        analyze: env.npm_config_analyze === 'true' || false,
        sentryToken: env.npm_config_sentry_token || '',
    };

    config.staticUrl = getStaticUrl(config);

    return config;
}

function getStaticUrl(config) {
    if (config.staticUrl) {
        return config.staticUrl;
    }

    if (config.env.prod) {
        var branchName = config.branchName.substring(0, 20);
        if (branchName === 'master') {
            branchName = '';
        }
        return (
            'https://one-static.zemanta.com/build-' +
            branchName +
            config.buildNumber +
            '/client'
        );
    }

    return 'http://localhost:9999';
}

var _root = path.resolve(__dirname, '..'); // eslint-disable-line no-undef
function root(args) {
    args = Array.prototype.slice.call(arguments, 0);
    return path.join.apply(path, [_root].concat(args));
}
