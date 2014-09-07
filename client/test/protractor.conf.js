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
    specs: ['e2e/scenarios.js'],
    rootElement: 'div',
    chromeOnly: true,
    baseUrl: localConfig.baseUrl, // only works when calling browser.get()

    onPrepare: function () {
        // handle signin
        browser.driver.get(localConfig.baseUrl + '/signin');
        browser.driver.findElement(By.name('username')).sendKeys(localConfig.signinUsername);
        browser.driver.findElement(By.name('password')).sendKeys(localConfig.signinPassword);
        browser.driver.findElement(By.id('id_signin_btn')).click();
    }
};
