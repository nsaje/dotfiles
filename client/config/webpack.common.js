var webpack = require('webpack');
var path = require('path');
var MiniCssExtractPlugin = require('mini-css-extract-plugin');
var FilterChunkWebpackPlugin = require('filter-chunk-webpack-plugin');

var APP_ENVIRONMENT = null;
var THEMES = {
    one: {name: 'one'},
    adtechnacity: {name: 'adtechnacity'},
    greenpark: {name: 'greenpark'},
    newscorp: {name: 'newscorp'},
    burda: {name: 'burda'},
    mediamond: {name: 'mediamond'},
    adyoulike: {name: 'adyoulike'},
    das: {name: 'das'},
};
var DEFAULT_THEME = THEMES.one;
var WHITELABELS = [
    THEMES.adtechnacity,
    THEMES.greenpark,
    THEMES.newscorp,
    THEMES.burda,
    THEMES.mediamond,
    THEMES.adyoulike,
    THEMES.das,
];

module.exports.DEFAULT_THEME = DEFAULT_THEME;
module.exports.getAppEnvironment = getAppEnvironment;
module.exports.getThemes = getThemes;
module.exports.getWhitelabels = getWhitelabels;
module.exports.generateMainConfig = generateMainConfig;
module.exports.generateStyleConfig = generateStyleConfig;
module.exports.root = root;

function getAppEnvironment() {
    if (!APP_ENVIRONMENT) {
        APP_ENVIRONMENT = generateAppEnvironment(process.env);
    }
    return APP_ENVIRONMENT;
}

function getThemes() {
    return THEMES;
}

function getWhitelabels() {
    return WHITELABELS;
}

function generateMainConfig(appEnvironment) {
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
            exclude: /node_modules/,
            use: [{loader: 'ng-annotate-loader'}],
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
            exclude: /node_modules/,
            loader: 'html-loader',
            options: {minimize: false},
        },
        {
            test: /\.css$/,
            sideEffects: true,
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
            loader: 'exports-loader?type=commonjs&exports=angular',
            include: [root('./lib/components/angular')],
        },
    ];

    config.plugins = [
        // Workaround for angular/angular#11580
        new webpack.ContextReplacementPlugin(
            // The (\\|\/) piece accounts for path separators in *nix and Windows
            /@angular(\\|\/)core/,
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
        new webpack.DefinePlugin({
            APP_ENVIRONMENT: JSON.stringify(appEnvironment),
        }),

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

function generateStyleConfig(appEnvironment, themeName) {
    var config = {
        module: {},
        plugins: [],
    };

    config.module.rules = [
        {
            test: /\.less$/,
            exclude: /node_modules/,
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
                        lessOptions: {
                            paths: [root('./one/app/themes/' + themeName)],
                            relativeUrls: false,
                            rootpath: appEnvironment.staticUrl + '/one/',
                        },
                    },
                },
                {
                    loader: 'style-resources-loader',
                    options: {
                        patterns: [root('./one/app/styles/icons/icons.less')],
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
            patterns: [
                '*.js',
                '*.txt',
                '*.map',
                '*.polyfills.css',
                '*.lib.css',
            ],
        }),
    ];

    return config;
}

// eslint-disable-next-line complexity
function generateAppEnvironment(env) {
    var config = {
        env: {
            dev: env.NODE_ENV === 'development' || !env.NODE_ENV,
            test: env.NODE_ENV === 'test',
            prod: env.NODE_ENV === 'production',
            e2e: env.NODE_ENV === 'e2e',
        },
        buildNumber: env.npm_config_build_number || '',
        branchName: env.npm_config_branch_name || '',
        theme: THEMES[env.npm_config_theme] || DEFAULT_THEME,
        analyze: env.npm_config_analyze === 'true' || false,
        sentryToken: env.npm_config_sentry_token || '',
        buildMainConfig: env.npm_config_build_main === 'true' || false,
        buildStyleConfig: env.npm_config_build_style === 'true' || false,
        buildWhitelabels: env.npm_config_build_whitelabels === 'true' || false,
        aot: env.npm_config_aot === 'true' || false,
    };

    config.staticUrl = getStaticUrl(config);

    return config;
}

function getStaticUrl(config) {
    if (config.staticUrl) {
        return config.staticUrl;
    }

    if (config.env.prod) {
        var branchName = config.branchName;
        if (branchName === 'master') {
            branchName = '';
        }
        return (
            'https://one-static.zemanta.com/build-' +
            branchName +
            config.buildNumber +
            '/client'
        );
    } else if (config.env.e2e) {
        return 'http://localhost:9898';
    }

    return 'http://localhost:9999';
}

var _root = path.resolve(__dirname, '..'); // eslint-disable-line no-undef
function root(args) {
    args = Array.prototype.slice.call(arguments, 0);
    return path.join.apply(path, [_root].concat(args));
}
