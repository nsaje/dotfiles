var fs = require('fs');
var path = require('path');

// load local config
if (!fs.existsSync(path.join(__dirname, 'protractor.localconf.json'))) {
    console.log('Create a protractor.localconf.json with your local configuration based on the protractor.localconf.json.template file.');
    process.exit(1);
} else {
    localConfig = require('./protractor.localconf.json');
}

exports.config = {
    specs: ['e2e/demo.js'],
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

        return browser.driver.wait(function() {
            return browser.driver.getCurrentUrl().then(function(url) {
                return /all_accounts\/accounts/.test(url);
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
