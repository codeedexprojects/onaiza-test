from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from registration.forms import RegistrationForm
from django.forms.widgets import TextInput, Textarea, Select, HiddenInput, FileInput, EmailInput
from users import models
from users.models import *
from dal import autocomplete




class UserForm(RegistrationForm):

    username = forms.CharField(label=_("Username"),
                               max_length=254,
                               widget=forms.TextInput(
        attrs={'placeholder': 'Enter username', 'class': 'required form-control'})
    )
    email = forms.EmailField(label=_("Email"),
                             max_length=254,
                             widget=forms.TextInput(
        attrs={'placeholder': 'Enter email', 'class': 'required form-control'})
    )
    password1 = forms.CharField(label=_("Password"),
                                widget=forms.PasswordInput(
                                    attrs={'placeholder': 'Enter password', 'class': 'required form-control'})
                                )
    password2 = forms.CharField(label=_("Repeat Password"),
                                widget=forms.PasswordInput(
                                    attrs={'placeholder': 'Enter password again', 'class': 'required form-control'})
                                )

    bad_domains = ['guerrillamail.com']

    def clean_email(self):
        email_domain = self.cleaned_data['email'].split('@')[1]
        if User.objects.filter(email__iexact=self.cleaned_data['email'], is_active=True):
            raise forms.ValidationError(
                _("This email address is already in use."))
        elif email_domain in self.bad_domains:
            raise forms.ValidationError(
                _("Registration using %s email addresses is not allowed. Please supply a different email address." % email_domain))
        return self.cleaned_data['email']

    min_password_length = 6

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1', '')
        if len(password1) < self.min_password_length:
            raise forms.ValidationError(
                "Password must have at least %i characters" % self.min_password_length)
        else:
            return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    min_username_length = 6

    def clean_username(self):
        username = self.cleaned_data['username']
        existing = User.objects.filter(
            username__iexact=self.cleaned_data['username'])
        if existing.exists():
            raise forms.ValidationError(
                _("A user with that username already exists."))
        elif len(username) < self.min_username_length:
            raise forms.ValidationError(
                "Username must have at least %i characters" % self.min_password_length)
        else:
            return self.cleaned_data['username']


class PhoneForm(forms.Form):
    phone = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'required form-control',
                'placeholder': 'Enter phone number',
                'type': 'number',
                'oninput': 'javascript: if (this.value.length > this.maxLength) this.value = this.value.slice(0, this.maxLength)',
                'maxlength': '10',
                'minlength': '10',
            }
        )
    )


class SignUpForm(forms.Form):

    username = forms.CharField(
        label=_("Username"),
        max_length=254,
        widget=TextInput(
            attrs={
                'placeholder': 'Enter username',
                'class': 'required user-input form-control'
            }
        )
    )
    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Enter email',
                'class': 'required user-input form-control'
            }
        )
    )
    password1 = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Enter password',
                'class': 'required form-control'
            }
        )
    )
    password2 = forms.CharField(
        label=_("Repeat Password"),
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Enter password again',
                'class': 'required form-control'
            }
        )
    )

    phone = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'required user-input form-control',
                'placeholder': 'Enter phone number',
                'type': 'number',
                'oninput': 'javascript: if (this.value.length > this.maxLength) this.value = this.value.slice(0, this.maxLength)',
                'maxlength': '10',
                'minlength': '10',
            }
        )
    )

    bad_domains = ['guerrillamail.com']

    def clean_email(self):
        email_domain = self.cleaned_data['email'].split('@')[1]

        if User.objects.filter(email__iexact=self.cleaned_data['email'], is_active=True):
            raise forms.ValidationError(
                _("This email address is already in use.")
            )
        elif email_domain in self.bad_domains:
            raise forms.ValidationError(
                _("Registration using %s email addresses is not allowed. Please supply a different email address." % email_domain))
        return self.cleaned_data['email']

    min_password_length = 6

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1', '')

        if len(password1) < self.min_password_length:
            raise forms.ValidationError(
                "Password must have at least %i characters" % self.min_password_length)
        else:
            return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                _("Password Mismatch."),
                code='password_mismatch',
            )
        return password2

    min_username_length = 6

    def clean_username(self):
        username = self.cleaned_data['username']
        existing = User.objects.filter(
            username__iexact=self.cleaned_data['username']
        )

        if existing.exists():
            raise forms.ValidationError(
                _("A user with that username already exists."))
        elif len(username) < self.min_username_length:
            raise forms.ValidationError(
                "Username must have at least %i characters" % self.min_password_length)
        else:
            return self.cleaned_data['username']

    def clean_phone(self):
        existing = models.RegistrationProfile.objects.filter(
            phone__iexact=self.cleaned_data['phone']
        )

        if existing.exists():
            raise forms.ValidationError(
                _("A user with that phone number already exists."))
        else:
            return self.cleaned_data['phone']


class OTPForm(forms.Form):
    otp = forms.CharField(
        widget=TextInput(
            attrs={
                'class': 'required user-input form-control',
                'placeholder': 'Enter OTP',
                'type': 'number',
                'oninput': 'javascript: if (this.value.length > this.maxLength) this.value = this.value.slice(0, this.maxLength)',
                'maxlength': '4',
                'minlength': '4',
            }
        )
    )


class LoginForm(forms.Form):

    username = forms.CharField(
        label=_("Username"),
        max_length=254,
        widget=TextInput(
            attrs={
                'placeholder': 'Enter username',
                'class': 'required user-input form-control'
            }
        )
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Enter password',
                'class': 'required form-control'
            }
        )
    )


class AddressForm(forms.ModelForm):

    pincode =  forms.ModelChoiceField(queryset=Location.objects.filter(is_deleted=False), required=False)

    class Meta:
        model = CustomerAddress
        exclude = [ 'is_deleted','customer','address_type','is_default']
        widgets = {
            'name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Name'}),
            'phone': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Phone'}),
            'email': EmailInput(attrs={'class': 'required form-control', 'placeholder': 'Email'}),

            'house_name': TextInput(attrs={'class': 'required form-control'}),
            'street': TextInput(attrs={'class': 'required form-control'}),
            'city': TextInput(attrs={'class': 'required form-control'}),
            'landmark': TextInput(attrs={'class': 'required form-control'}),
            'state': TextInput(attrs={'class': 'required form-control'}),
        }

        error_messages = {

        }