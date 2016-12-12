/* globals require, __dirname, process, localConfig, exports, browser, By */

var fs = require('fs');
var path = require('path');

// load local config
if (!fs.existsSync(path.join(__dirname, 'protractor.localconf.json'))) {
    console.log('Create a protractor.localconf.json with your local configuration based on the protractor.localconf.json.template file.'); // eslint-disable-line no-console
    process.exit(1);
} else {
    localConfig = require('./protractor.localconf.json'); // eslint-disable-line no-global-assign
}

exports.config = {
    specs: ['e2e/scenarios.js'],
    rootElement: 'div',
    chromeOnly: true,
    baseUrl: localConfig.baseUrl, // only works when calling browser.get()

    onPrepare: function () {
        // handle signin
        browser.ignoreSynchronization = true;
        browser.driver.get(localConfig.baseUrl + '/signin');
        browser.driver.findElement(By.id('id_username')).sendKeys('protractor@zemanta.com');
        browser.driver.findElement(By.id('id_password')).sendKeys('testPr0tr4ct0r');
        browser.driver.findElement(By.id('id_signin_btn')).click();

        return browser.driver.wait(function () {
            return browser.driver.getCurrentUrl().then(function (url) {
                return /accounts\/[0-9]+\/campaigns/.test(url);
            });
        }, 10000);
    },

    framework: 'jasmine',
    jasmineNodeOpts: {
        isVerbose: true,
        showColors: true,
        includeStackTrace: true,
        defaultTimeoutInterval: 60000
    }
};
