from django import forms

class RawQueryForm(forms.Form):
    raw_query = forms.CharField(label='raw query', max_length=256)