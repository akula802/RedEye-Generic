# Core library imports

# 3rd-party imports
from django.contrib.auth.tokens import PasswordResetTokenGenerator
#from django.utils import six
import six

# Local app imports


# Part of the 'user signup with email confirmation' tutorial
# https://medium.com/@frfahim/django-registration-with-confirmation-email-bb5da011e4ef
# class TokenGenerator(PasswordResetTokenGenerator):
#     def _make_hash_value(self, user, timestamp):
#         return (
#             six.text_type(user.pk) + six.text_type(timestamp) +
#             six.text_type(user.is_active)
#         )
# account_activation_token = TokenGenerator()



# From: https://pylessons.com/django-email-confirm
class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp)  + six.text_type(user.is_active)
        )

account_activation_token = AccountActivationTokenGenerator()

