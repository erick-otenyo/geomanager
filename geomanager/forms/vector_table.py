from django import forms


class VectorTableForm(forms.Form):
    columns = forms.JSONField(required=False, widget=forms.HiddenInput)
