


class GASourceAuth(object):
    
    def __init__(self, email):
        self.email = email

    def is_authorised(self):
        return True
        
        
class MailGunRequestAuth(object):
    
    def __init__(self, request):
        self.request = request
    
    def is_authorised(self):
        return True
