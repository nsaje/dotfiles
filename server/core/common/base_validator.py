class BaseValidator(object):

    """ Make `save` call `full_clean`.
    .. warning:
        This should be the left-most mixin/super-class of a model.
    """

    def clean(self):
        """ Override to validate the model """
        pass

    def save(self, *args, **kwargs):
        """ Call `full_clean` before saving. """
        self.full_clean()
        super(BaseValidator, self).save(*args, **kwargs)
