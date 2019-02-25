from . import exceptions


class AudienceValidatorMixin(object):
    def clean(self, changes):
        self._validate_archived(changes)

    def _validate_archived(self, changes):
        if "archived" in changes and changes["archived"] and not self.can_archive():
            raise exceptions.CanNotArchive(
                "Audience '{name}' is currently targeted on ad groups {adgroups}.".format(
                    name=self.name, adgroups=", ".join([ad.name for ad in self.get_ad_groups_using_audience()])
                )
            )
