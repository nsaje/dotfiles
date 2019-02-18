class FacebookAccountMixin:
    def __str__(self):
        return self.account.name
