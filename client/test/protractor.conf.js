exports.config = {
    seleniumAddress: 'http://localhost:4444/wd/hub',
    specs: ['e2e/scenarios.js'],
    rootElement: 'div',
    chromeOnly: true,

    onPrepare: function () {
        // handle signin
        browser.driver.get('http://localhost:8000/');
        browser.driver.findElement(By.name('username')).sendKeys('florjan.bartol@gmail.com');
        browser.driver.findElement(By.name('password')).sendKeys('wafelj88');
        browser.driver.findElement(By.id('id_signin_btn')).click();
    }
}
