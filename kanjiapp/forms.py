from django import forms


class SearchForm(forms.Form):
    text = forms.CharField(label="解析対象")