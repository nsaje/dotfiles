from . import constants
from . import exceptions


class UserValidationMixin(object):
    def clean(self):
        super().clean()
        self._validate_email()

    def validate(self, changes):
        self._validate_country(changes)
        self._validate_company_type(changes)
        self._validate_start_year_of_experience(changes)

    def _validate_email(self):
        if not self.pk and self.__class__.objects.filter(email=self.email.lower).exists():
            raise exceptions.EmailAlreadyExists("User with this e-mail already exists.")

    @staticmethod
    def _validate_country(changes):
        country = changes.get("country")
        if country is None:
            return
        if country not in constants.Country.get_all():
            raise exceptions.InvalidCountry("Select a valid country.")

    @staticmethod
    def _validate_company_type(changes):
        company_type = changes.get("company_type")
        if company_type is None:
            return
        if company_type not in constants.CompanyType.get_all():
            raise exceptions.InvalidCompanyType("Select a valid company type.")

    @staticmethod
    def _validate_start_year_of_experience(changes):
        start_year_of_experience = changes.get("start_year_of_experience")
        if start_year_of_experience is None:
            return
        if start_year_of_experience not in constants.Year.get_all():
            raise exceptions.InvalidStartYearOfExperience("Select a valid start year of experience.")
