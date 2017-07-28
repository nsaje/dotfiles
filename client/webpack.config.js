/* globals require, process, __dirname */

var path = require('path');
var webpack = require('webpack');
var merge = require('webpack-merge');
var ExtractTextPlugin = require('extract-text-webpack-plugin');
var CopyWebpackPlugin = require('copy-webpack-plugin');

var ENVIRONMENTS = {
    DEVELOPMENT: 'dev',
    PRODUCTION: 'prod',
    TEST: 'tests',
    TEST_WATCH: 'tests-watch'
};

var ENV = process.env.npm_lifecycle_event;
var BUILD_NUMBER = process.env['npm_config_build_number'];
var IS_WHITELABEL = process.env['npm_config_whitelabel'];

var STATIC_URL = ENV === ENVIRONMENTS.PRODUCTION ?
    'https://one-static.zemanta.com/build-' + BUILD_NUMBER + '/client' : 'http://localhost:9999';

var APP_CONFIG = {
    staticUrl: STATIC_URL,
    env: {
        dev: ENV === ENVIRONMENTS.DEVELOPMENT,
        test: ENV === ENVIRONMENTS.TEST || ENV === ENVIRONMENTS.TEST_WATCH,
        prod: ENV === ENVIRONMENTS.PRODUCTION,
    },
    buildNumber: BUILD_NUMBER,
};

//
// Webpack configuration
//
var config = {};

config.entry = {
    'zemanta-one.polyfills': './one/polyfills.ts',
    'zemanta-one.lib': './one/vendor.ts',
    'zemanta-one': './one/main.ts',
};

config.output = {
    path: path.join(__dirname, 'dist/one'),
    publicPath: 'one/',
    filename: '[name].js',
    sourceMapFilename: '[file].map',
};

config.plugins = [
    // Workaround for angular/angular#11580
    new webpack.ContextReplacementPlugin(
        // The (\\|\/) piece accounts for path separators in *nix and Windows
        /angular(\\|\/)core(\\|\/)@angular/,
        './one/', // location of your src
        {} // a map of your routes
    ),

    // Join all CSS output into one file; based on the entry name
    new ExtractTextPlugin('[name].css'),

    // Define application configuration; used by config module
    new webpack.DefinePlugin({APP_CONFIG: JSON.stringify(APP_CONFIG)}),

    // Fix issue with moment.js locales - by default all locales are added (~30k loc)
    new webpack.ContextReplacementPlugin(/moment[\/\\]locale$/, /en/),

    new webpack.ProvidePlugin({
        $: 'jquery',
        jQuery: 'jquery',
        'window.jQuery': 'jquery',
        moment: 'moment',
    }),
];

config.module = {};
config.module.rules = [
    {
        // Webpack loader to annotate angular applications. Generates a sourcemaps as well.
        test: /\.js$/,
        include: [path.resolve(__dirname, 'one/app')],
        use: [{loader: 'ng-annotate-loader'}],
    }, {
        test: /\.tsx?$/,
        loader: 'ts-loader',
        options: {
            logLevel: 'warn',
        }
    }, {
        // Allow loading html through js
        test: /\.html$/,
        loader: 'html-loader',
        options: {
            minimize: ENV === ENVIRONMENTS.PRODUCTION,
        }
    }, {
        test: /\.css$/,
        use: ExtractTextPlugin.extract({
            fallback: 'style-loader',
            use: [
                {loader: 'css-loader'}
            ]
        })
    }, {
        test: /\.(png|jpg|jpeg|gif|svg|woff|woff2|ttf|eot)$/,
        loader: 'url-loader',
    }
];

//
// Workarounds FIXME: replacing Bower with NPM will resolve this issues
//
config.module.rules.push(
    {
        // Workaround: Convert AngularJS to CommonJS module
        test: /angular\.js$/, loader: 'exports-loader?angular',
        include: [path.resolve(__dirname, 'lib/components/angular')]
    }
);

config.resolve = {
    extensions: ['.ts', '.js'],
    modules: [path.resolve('./one'), 'node_modules'],
    alias: {
        'angular': path.resolve(__dirname, 'lib/components/angular/angular.js'),
        'jquery': path.resolve(__dirname, 'lib/components/jquery/dist/jquery.js'),
        'moment': path.resolve(__dirname, 'lib/components/moment/moment.js'),
    },
};


//
// Styles - zOne and whitelabels
//
function styleConfig (style) {
    var entryModule = style + '.styles.webpack.js';
    var entryname = style === 'one' ? 'zemanta-one' : 'zemanta-one-' + style;

    var entry = {};
    entry[entryname] = './one/app/styles/' + entryModule;
    var stylePath = path.resolve(__dirname, './one/app/styles/' + style);

    return {
        entry: entry,
        module: {
            rules: [
                {
                    // Import shared.less to each less file
                    test: /\.less$/,
                    enforce: 'pre',
                    loader: 'webpack-append',
                    query: '@import \'shared\';',
                    include: [path.resolve(__dirname, 'one/app')]
                },
                {
                    test: /\.less$/,
                    use: ExtractTextPlugin.extract({
                        fallback: 'style-loader',
                        use: [
                            {
                                loader: 'css-loader', options: {
                                    url: false,
                                    minimize: ENV === ENVIRONMENTS.PRODUCTION,
                                }
                            },
                            {
                                loader: 'less-loader',
                                options: {
                                    paths: [stylePath],
                                    relativeUrls: false,
                                    rootpath: ENV === ENVIRONMENTS.PRODUCTION ? STATIC_URL + '/one/' : ''
                                }
                            }
                        ]
                    }),
                }
            ]
        },
        plugins: [
            new ExtractTextPlugin('[name].css'),
        ]
    };
}

//
// Environment setup - Development, Test, Production
//
if (ENV === ENVIRONMENTS.DEVELOPMENT) {
    config = merge.smart(config, styleConfig('one'));
    config.entry['zemanta-one'] = ['./one/main.ts', './one/app/styles/one.styles.webpack.js'];

    if (IS_WHITELABEL) {
        // TODO
    }

    config.devtool = 'cheap-module-eval-source-map';
    config.devServer = {
        contentBase: './',
        stats: 'minimal',
        disableHostCheck: true,
        watchOptions: {
            ignored: /node_modules|.*spec\.js|.*mock\.js|.*spec\.ts|.*mock\.ts/,
            aggregateTimeout: 300,
            poll: 1000
        },
    };
}

if (ENV === ENVIRONMENTS.TEST || ENV === ENVIRONMENTS.TEST_WATCH) {
    config.devtool = 'inline-source-map';
}

if (ENV === ENVIRONMENTS.PRODUCTION) {
    config.devtool = 'source-map';
    config.plugins.push(
        new webpack.optimize.CommonsChunkPlugin({
            name: ['zemanta-one', 'zemanta-one.lib', 'zemanta-one.polyfills']
        }),
        new webpack.optimize.ModuleConcatenationPlugin(),
        new webpack.optimize.UglifyJsPlugin({
            comments: false,
            sourceMap: true
        }),
        new CopyWebpackPlugin([
            {
                from: __dirname + '/one/images',
                to: 'images'
            },
            {
                from: __dirname + '/one/assets',
                to: 'assets'
            }
        ])
    );

    config = [
        config,
        merge.smart(config, styleConfig('one')),
        merge.smart(config, styleConfig('greenpark')),
        merge.smart(config, styleConfig('adtechnacity')),
        merge.smart(config, styleConfig('newscorp')),
    ];
}

module.exports = config;


