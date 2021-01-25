var common = require('./webpack.common.js');
var ForkTsCheckerWebpackPlugin = require('fork-ts-checker-webpack-plugin');

var appEnvironment = common.getAppEnvironment();
var configs = [];

var config = generateConfig(appEnvironment, appEnvironment.theme.name);
configs.push(config);

module.exports = configs;

function generateConfig(appEnvironment) {
    var config = common.generateMainConfig(appEnvironment);

    config.module.rules = [
        {
            // Angular TypeScript and template loaders
            test: /\.tsx?$/,
            exclude: /node_modules/,
            use: [
                {
                    loader: 'awesome-typescript-loader',
                    options: {
                        transpileOnly: true,
                        configFileName: 'tsconfig.test.json',
                    },
                },
                {loader: 'angular2-template-loader'},
            ],
        },
        {
            // https://github.com/angular/universal-starter/pull/593/commits/644c5f6f28a760f94ef111f5a611e2c9ed679b6a
            // Mark files inside `@angular/core` as using SystemJS style dynamic imports.
            // Removing this will cause deprecation warnings to appear.
            test: /(\\|\/)@angular(\\|\/)core(\\|\/).+\.js$/,
            parser: {system: true},
        },
        {
            test: /\.html$/,
            loader: 'html-loader',
        },
        {
            test: /\.css$/,
            use: 'null-loader',
        },
        {
            test: /\.less$/,
            use: 'null-loader',
        },
        {
            // Workaround: Convert AngularJS to CommonJS module
            test: /angular\.js$/,
            loader: 'exports-loader?type=commonjs&exports=angular',
            include: [common.root('./lib/components/angular')],
        },
    ];

    config.plugins = config.plugins.concat([
        // https://github.com/TypeStrong/fork-ts-checker-webpack-plugin
        // Runs typescript type checking in a separate process.
        new ForkTsCheckerWebpackPlugin(),
    ]);

    config.mode = 'development';

    return config;
}
