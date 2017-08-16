var webpack = require('webpack');
var CopyWebpackPlugin = require('copy-webpack-plugin');
var merge = require('webpack-merge');
var common = require('./webpack.common.js');

var prodConfigs = [];
var buildConfig = common.getBuildConfig();

// Main app config
var mainProdConfig = generateMainProdConfig(common.generateMainConfig(buildConfig));
prodConfigs.push(mainProdConfig);

// Themes configs
var themes = common.getThemes();
Object.keys(themes).forEach(function (key) {
    prodConfigs.push(generateStyleProdConfig(common.generateMainConfig(buildConfig), themes[key]));
});

module.exports = prodConfigs;

function generateMainProdConfig (mainConfig) {
    var mainProdConfig = mainConfig;

    mainProdConfig.entry = {
        'zemanta-one.polyfills': common.root('./one/polyfills.ts'),
        'zemanta-one.lib': common.root('./one/vendor.ts'),
        'zemanta-one': common.root('./one/main.ts'),
    };

    mainProdConfig.output = {
        path: common.root('./dist/one'),
        publicPath: 'one/',
        filename: '[name].js',
        sourceMapFilename: '[file].map',
    };

    // Skip loading styles as they are extracted separately by ExtractTextPlugin defined in styleProdConfigs
    mainProdConfig.module.rules.push({
        test: /\.less$/,
        loader: 'null-loader',
    });

    mainProdConfig.plugins = mainProdConfig.plugins.concat([
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
                from: common.root('./one/images'),
                to: 'images'
            },
            {
                from: common.root('./one/assets'),
                to: 'assets'
            }
        ])
    ]);

    mainProdConfig.devtool = 'source-map';

    return mainProdConfig;
}

function generateStyleProdConfig (mainConfig, theme) {
    var styleConfig = common.generateStyleConfig(theme);
    var styleProdConfig = merge.smart(mainConfig, styleConfig);

    styleProdConfig.entry = [common.root('./one/app/styles/main.less'), common.root('./one/main.ts')];

    // Ignore output, compiled styles are extracted by ExtractTextPlugin and saved as zemanta-one[-theme].css
    styleProdConfig.output = {
        path: common.root('./dist/one'),
        filename: 'ignored',
    };

    return styleProdConfig;
}

