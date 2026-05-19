from django import forms
from .models import UserRegistrationModel


class UserRegistrationForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={'pattern': '[a-zA-Z]+'}), required=True, max_length=100)
    loginid = forms.CharField(widget=forms.TextInput(attrs={'pattern': '[a-zA-Z]+'}), required=True, max_length=100)
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'pattern': '(?=.*[a-z])(?=.*[A-Z]).{6,}',
        'title': 'Must contain at least one uppercase and one lowercase letter, and at least 6 characters'
    }), required=True, max_length=100)

    mobile = forms.CharField(widget=forms.TextInput(attrs={
        'pattern': '[6-9][0-9]{9}',
        'title': 'Mobile number must start with 6-9 and be 10 digits'
    }), required=True, max_length=10)

    email = forms.CharField(widget=forms.TextInput(attrs={
        'pattern': '[a-z0-9._%+-]+@gmail\.com$',
        'title': 'Only Gmail addresses are allowed'
    }), required=True, max_length=100)

    locality = forms.CharField(widget=forms.TextInput(), required=True, max_length=100)
    address = forms.CharField(widget=forms.TextInput(), required=True, max_length=250)
    city = forms.CharField(widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'pattern': '[A-Za-z ]+', 'title': 'Enter Characters Only '}), required=True,
        max_length=100)
    state = forms.CharField(widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'pattern': '[A-Za-z ]+', 'title': 'Enter Characters Only '}), required=True,
        max_length=100)
    status = forms.CharField(widget=forms.HiddenInput(), initial='waiting', max_length=100)

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not any(char.isupper() for char in password):
            raise forms.ValidationError('Password must contain at least one uppercase letter.')
        if not any(char.islower() for char in password):
            raise forms.ValidationError('Password must contain at least one lowercase letter.')
        if len(password) < 6:
            raise forms.ValidationError('Password must be at least 6 characters long.')
        return password

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')
        if not mobile.isdigit() or len(mobile) != 10 or mobile[0] not in '6789':
            raise forms.ValidationError('Enter a valid 10-digit mobile number starting with 6-9.')
        return mobile

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if not email.endswith('@gmail.com'):
            raise forms.ValidationError('Only Gmail addresses are allowed.')
        return email

    class Meta():
        model = UserRegistrationModel
        fields = '__all__'