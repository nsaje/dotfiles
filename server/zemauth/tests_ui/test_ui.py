import unittest

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from statsd.defaults.django import statsd

from django.conf import settings

from utils import test_decorators


LOGIN_TEST_USERNAME = 'one-test@zemanta-test.com'
LOGIN_TEST_PASSWORD = 'thisISaT45est-passw0rd'


@test_decorators.health_check
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
        try:
            self.driver.get('https://one.zemanta.com/signin')

            wait = WebDriverWait(self.driver, 10)
            wait.until(lambda driver: driver.find_element_by_id('id_signin_btn'))

            email_input = self.driver.find_element_by_id('id_username')
            email_input.send_keys(LOGIN_TEST_USERNAME)

            password_input = self.driver.find_element_by_id('id_password')
            password_input.send_keys(LOGIN_TEST_PASSWORD)

            signin_btn = self.driver.find_element_by_id('id_signin_btn')
            signin_btn.submit()

            expected_url = 'https://one.zemanta.com/'
            wait.until(lambda driver: driver.current_url == expected_url)
        except:
            self.fail('Could not sign in.')

        statsd.incr('one.auth.login.health_check_ok')
