APT stands for Automatic Production Tests. The purpose of these tests is to perform checks
on production data to increase developers' confindence that the system is working
correctly. They are run using readonly database users in order to avoid accidentally
changing production data.

# Running the tests suite

A custom django command `apt_test` in this app exists to run the suite or any specific test
within the suite. It is important to set the environment variable `CONF_ENV` to `apt` in
order for the right localsettings to be loaded otherwise the command will be terminated
with an error.

```
CONF_ENV=apt ./manage.py apt_test
```

Running a specific test (case) is supported as in django. It's also possible to specify
multiple tests/test cases separated with a space.

```
CONF_ENV=apt ./manage.py apt_test apt.tests.test_example.ExampleAPTTest.test_example_db
```

# Adding tests

The framework is set up to only search for tests within this folder - `apt`. New tests
should be added into `apt/tests` folder and the files should be prefixed with `test_`,
otherwise the test runner will not search for them.

Tests should sublclass `apt.base.test_case.APTTestCase`. The test runner will only run
tests in such test cases. They will also be ignored by the project's unit test runner.
