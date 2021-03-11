# NOTICE
#
# This software was produced for the U. S. Government
# under Basic Contract No. W15P7T-13-C-A802, and is
# subject to the Rights in Noncommercial Computer Software
# and Noncommercial Computer Software Documentation
# Clause 252.227-7014 (FEB 2012)
#
# (C) 2017 The MITRE Corporation.

# Global imports
import datetime
import logging
import re

import smtplib
from itsdangerous import BadSignature, URLSafeTimedSerializer
from mongoengine import Document, EmbeddedDocumentField, ListField, StringField, EmailField
from passlib.hash import sha256_crypt
from email.mime.text import MIMEText

from app.utils import AuthenticationError
from app.cascade.query_layers.base import DataModelQueryLayer, UserDatabaseInfo
from app import settings


logger = logging.getLogger(__name__)
enable_creation = True

serializer = None  # type: URLSafeTimedSerializer


def get_serializer():
    global serializer
    if serializer is None:
        serializer = URLSafeTimedSerializer(settings.load()['database']['crypto']['key'])
    return serializer


default_timeout = datetime.timedelta(days=7)
reset_password_timeout = datetime.timedelta(minutes=60)

loaded_users = {}
""":type dict[str, User]"""


class PasswordPolicyError(ValueError):
    pass


class User(Document, DataModelQueryLayer):
    username = StringField(required=True)
    sha256_hash = StringField()
    full_name = StringField()
    databases = ListField(EmbeddedDocumentField(UserDatabaseInfo))
    email = EmailField()

    def __init__(self, *args, **kwargs):
        super(Document, self).__init__(*args, **kwargs)
        self._layers = {}

    def login(self):
        if self.id in loaded_users:
            user = loaded_users[self.id]
            old_databases = user.databases
        else:
            user = self
            old_databases = []

        user.databases = self.databases

        # remove any databases that are no longer present or have changed
        for db_info in old_databases:
            if db_info not in user.databases:
                user.detach_layer(db_info)

        # update any databases that have changed or been added (attach_layer will overwrite)
        for db_info in user.databases:
            if db_info not in old_databases:
                user.attach_layer(db_info)

        # Add to memory to avoid creating these objects again
        loaded_users[user.username] = user
        loaded_users[user.id] = user
        return user

    def set_password(self, value):
        password_config = settings.load().get('password', None)
        if password_config and password_config.get('enforce'):
            regex = password_config['regex']
            rules = password_config.get('rules', [])
            if re.match(regex, value) is None:
                raise PasswordPolicyError(regex, rules)
        self.sha256_hash = sha256_crypt.encrypt(value)

    @property
    def layers(self):
        query_layers = []
        for db_info, query_layer in self._layers.values():
            query_layers.append(query_layer)

        return tuple(query_layers)

    def add_layer(self, database_info):
        """ Add the database connector to the user object
        :type database_info: UserDatabaseInfo
        """
        # first, confirm that a login is possible
        self.attach_layer(database_info)
        self.modify(add_to_set__databases=database_info)
        return True

    def remove_layer(self, database_id):
        """ Remove the database connector from the user object
        """
        if database_id in self._layers:
            database_info, query_layer = self._layers[database_id]
            self.detach_layer(database_id)
            self.modify(pull__databases=database_info)
            return True
        else:
            return False

    def attach_layer(self, database_info):
        """ Attach a query layer, based off of the database name
        :type database_info: QueryLayerInfo """
        query_layer = database_info.login()
        self._layers[database_info.database.id] = (database_info, query_layer)
        return query_layer

    def detach_layer(self, database_id):
        layer = self._layers.pop(database_id, None)
        return layer is not None

    def logout(self):
        """ This really doesn't do much but the server should remove the cookie elsewhere. This object could be
        purged from memory, but that would potentially be a bad idea, if one user is logged in via multiple locations.
        """
        loaded_users.pop(self.id, None)
        loaded_users.pop(self.username, None)
        return True

    def revoke_token(self, token):
        raise NotImplementedError()

    def generate_token(self, persistent=False):
        return get_serializer().dumps({'username': self.username, 'persistent': persistent})

    def generate_reset_token(self):
        return get_serializer().dumps({'username': self.username, 'action': 'reset'})

    def generate_reset_link(self):
        base_url = settings.load()['server']['url']
        url = "{}/#/reset-password?token={}".format(base_url, self.generate_reset_token())
        return url

    def send_reset_email(self):
        expires = datetime.datetime.now() + reset_password_timeout
        url = self.generate_reset_link()
        body = ("A password reset for {} has been requested.\r\n".format(self.username),
                "Navigate to {} to complete reset.".format(url),
                "Expires on {}".format(expires.isoformat())
                )
        message = MIMEText('\r\n'.join(body))
        message['Subject'] = "Password Reset Link for CASCADE on {}".format(settings.load()['server']['hostname'])
        message['From'] = 'cascade@' + settings.load()['server']['hostname']
        message['To'] = self.email

        server = smtplib.SMTP(settings.load()['links']['smtp'])
        server.set_debuglevel(1)
        server.sendmail(message['From'], [self.email], message.as_string())
        server.quit()

    def query(self, expression, **kwargs):
        for query_layer in self.layers:
            try:
                results = query_layer.query(expression, **kwargs)
                for result in results:
                    yield result
                raise StopIteration()
            except NotImplementedError:
                continue
        else:
            # todo: run locally as a fallback??
            logger.warn('No query layers for user {} support {}.'.format(self.username, expression))
            raise StopIteration()

    @property
    def external_analytics(self):
        for query_layer in self.layers:
            try:
                return query_layer.analytics
            except NotImplementedError:
                pass
        else:
            raise StopIteration()


def create_user(username, password, email=None, full_name=None):
    """
    :param str username: The username
    :param str password: The clear text password. Upon creation a safe/salted hash will be stored in the database
    :param str email: jdoe@mitre.org
    :param str full_name: John Doe
    :rtype: User
    """
    if User.objects(username=username).first() is None:
        user = User(username=username, email=email, full_name=full_name)
        user.set_password(password)
        user.save()
        return user


def reset_password(token, password):
    try:
        user_info = get_serializer().loads(token, max_age=reset_password_timeout.total_seconds())
    except BadSignature:
        raise AuthenticationError("Invalid token or token expired")

    if user_info.pop('action') != 'reset':
        raise AuthenticationError("Invalid token for password resets")

    user = User.objects(**user_info).first()
    if user is None:
        raise AuthenticationError("User not found")

    user.set_password(password)
    user.save()
    return user


def validate_token(token, timeout=default_timeout):
    """
    :param token: the URL Safe token, generated via User.generate_token
    :param datetime.timedelta timeout: The expiration time from the token
    :rtype: User
    """
    # If an exception happens, this must be handled by the caller
    try:
        user_info = get_serializer().loads(token)
    except BadSignature:
        raise AuthenticationError("Invalid token")

    # Persistent last indefinitely
    persistent = user_info.pop('persistent')
    if not persistent:
        user_info = get_serializer().loads(token, max_age=timeout.total_seconds())
        user_info.pop('persistent')

    # Don't fetch to mongo if not necessary
    user = User.objects(**user_info).first()
    if user is None:
        raise AuthenticationError("User not found")
    return user.login()


def login(username, password):
    user = User.objects(username=username).first()
    if user is None:
        raise AuthenticationError("Invalid user")

    elif not sha256_crypt.verify(password, user.sha256_hash):
        raise AuthenticationError("Invalid password")

    else:
        return user.login()
