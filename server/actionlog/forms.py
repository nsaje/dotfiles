from django import forms


class SourcePixelForm(forms.Form):
    url = forms.CharField(required=True)
    source_pixel_id = forms.CharField(required=True)
