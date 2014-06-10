import os
import unittest

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from statsd.defaults.django import statsd

from django.conf import settings


LOGIN_TEST_USERNAME = 'one-test@zemanta.com'
LOGIN_TEST_PASSWORD = 'thisISaT45est-passw0rd'


@unittest.skipIf(os.environ.get('HEALTH_CHECK', '0') == '0', 'Skipping health check tests.')
class LoginTestCase(unittest.TestCase):
    def setUp(self):
        desired_capabilities = webdriver.DesiredCapabilities.CHROME
        desired_capabilities['platform'] = 'Windows 8'
        desired_capabilities['name'] = 'Zemanta One Sign In Test'

        executor_url = 'http://{0}:{1}@ondemand.saucelabs.com:80/wd/hub'.format(
            settings.SAUCELABS_USERNAME, settings.SAUCELABS_ACCESS_KEY)

        self.driver = webdriver.Remote(
            desired_capabilities=desired_capabilities,
            command_executor=executor_url
        )

        self.driver.implicitly_wait(30)

    def tearDown(self):
        self.driver.quit()

    def test_login(self):
        self.driver.get('https://one.zemanta.com/signin')

        wait = WebDriverWait(self.driver, 10)
        try:
            wait.until_not(lambda browser: browser.find_element_by_id('id_signin_btn'))
        except TimeoutException:
            statsd.incr('one.auth.login.health_check_err')
            self.fail('Could not sign in.')

        email_input = self.driver.find_element_by_id('id_username')
        email_input.send_keys(LOGIN_TEST_USERNAME)

        password_input = self.driver.find_element_by_id('id_password')
        password_input.send_keys(LOGIN_TEST_PASSWORD)

        signin_btn = self.driver.find_element_by_id('id_signin_btn')
        signin_btn.submit()

        try:
            expected_url = 'https://one.zemanta.com'
            wait.until_not(lambda browser: browser.current_url == expected_url)
        except TimeoutException:
            statsd.incr('one.auth.login.health_check_err')
            self.fail('Could not sign in.')
