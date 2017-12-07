var path = require('path');
var ExtractTextPlugin = require('extract-text-webpack-plugin');
var webpack = require('webpack');

// FIXME (jurebajt): Create APP_CONFIG to push to app
var BUILD_CONFIG = null;
var THEMES = {
    one: {name: 'one'},
    adtechnacity: {name: 'adtechnacity'},
    greenpark: {name: 'greenpark'},
    newscorp: {name: 'newscorp'},
    burda: {name: 'burda'},
};

module.exports.getBuildConfig = getBuildConfig;
module.exports.getTheme = getTheme;
module.exports.getThemes = getThemes;
module.exports.generateMainConfig = generateMainConfig;
module.exports.generateStyleConfig = generateStyleConfig;
module.exports.root = root;

function getBuildConfig () {
    if (!BUILD_CONFIG) {
        BUILD_CONFIG = generateBuildConfig(process.env);
    }
    return BUILD_CONFIG;
}

function getTheme (name) {
    return THEMES[name] || THEMES.one;
}

function getThemes () {
    return THEMES;
}

function generateMainConfig (appConfig) {
    var config = {
        module: {},
    };
    var vendorExtractTextPlugin = new ExtractTextPlugin('[name].css');

    config.resolve = {
        extensions: ['.ts', '.js'],
        modules: [root('./one'), 'node_modules'],
        alias: {
            'angular': root('./lib/components/angular/angular.js'),
            'jquery': root('./lib/components/jquery/dist/jquery.js'),
            'moment': root('./lib/components/moment/moment.js'),
        },
    };

    config.module.rules = [
        {
            // Webpack loader to annotate angular applications. Generates a sourcemaps as well.
            test: /\.js$/,
            include: [root('./one/app/ajs-app')],
            use: [{loader: 'ng-annotate-loader'}],
        }, {
            // Angular TypeScript and template loaders
            test: /\.tsx?$/,
            loaders: [
                'awesome-typescript-loader',
                'angular2-template-loader',
            ],
        }, {
            // Allow loading html through js
            test: /\.html$/,
            loader: 'html-loader',
        }, {
            test: /\.css$/,
            use: vendorExtractTextPlugin.extract({
                fallback: 'style-loader',
                use: [
                    {loader: 'css-loader'}
                ]
            }),
        }, {
            test: /\.(png|jpg|jpeg|gif|svg|woff|woff2|ttf|eot)$/,
            loader: 'url-loader',
        }, {
            // Workaround: Convert AngularJS to CommonJS module
            test: /angular\.js$/, loader: 'exports-loader?angular',
            include: [root('./lib/components/angular')]
        },
    ];

    config.plugins = [
        // Workaround for angular/angular#11580
        new webpack.ContextReplacementPlugin(
            // The (\\|\/) piece accounts for path separators in *nix and Windows
            /angular(\\|\/)core(\\|\/)(@angular|esm5)/,
            root('./one'), // location of your src
            {} // a map of your routes
        ),

        // Join all CSS output into one file; based on the entry name
        vendorExtractTextPlugin,

        // Define application configuration
        new webpack.DefinePlugin({APP_CONFIG: JSON.stringify(appConfig)}),

        // Fix issue with moment.js locales - by default all locales are added (~30k loc)
        new webpack.ContextReplacementPlugin(/moment[/\\]locale$/, /en/),

        new webpack.ProvidePlugin({
            $: 'jquery',
            jQuery: 'jquery',
            'window.jQuery': 'jquery',
            moment: 'moment',
        }),
    ];

    return config;
}

function generateStyleConfig (theme) {
    var config = {
        module: {},
        plugins: [],
    };

    var output = 'zemanta-one';
    if (theme !== THEMES.one) {
        output = output + '-' + theme.name;
    }

    var extractTextPlugin = new ExtractTextPlugin(output + '.css');
    var rootpath = BUILD_CONFIG.staticUrl + '/one/';
    config.module.rules = [
        {
            test: /\.less$/,
            use: extractTextPlugin.extract({
                fallback: 'style-loader',
                use: [
                    {
                        loader: 'css-loader', options: {
                            url: false,
                            minimize: BUILD_CONFIG.env.prod,
                        }
                    },
                    {
                        loader: 'less-loader',
                        options: {
                            paths: [root('./one/app/themes/' + theme.name)],
                            relativeUrls: false,
                            rootpath: rootpath,
                        }
                    }
                ]
            })
        },
    ];
    config.plugins.push(extractTextPlugin);

    return config;
}

function generateBuildConfig (env) {
    var config = {
        env: {
            dev: env.NODE_ENV === 'development' || !env.NODE_ENV,
            test: env.NODE_ENV === 'test',
            prod: env.NODE_ENV === 'production',
        },
        buildNumber: env.npm_config_build_number,
        theme: env.npm_config_theme,
    };

    config.staticUrl = getStaticUrl(config);

    return config;
}

function getStaticUrl (config) {
    if (config.staticUrl) {
        return config.staticUrl;
    }

    if (config.env.prod) {
        return 'https://one-static.zemanta.com/build-' + config.buildNumber + '/client';
    }

    return 'http://localhost:9999';
}

var _root = path.resolve(__dirname, '..'); // eslint-disable-line no-undef
function root (args) {
    args = Array.prototype.slice.call(arguments, 0);
    return path.join.apply(path, [_root].concat(args));
}
