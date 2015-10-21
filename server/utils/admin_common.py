class SaveWithRequestMixin(object):
    def save_model(self, request, obj, form, change):
        obj.save(request)
