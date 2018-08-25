# -*- coding: utf-8 -*-
import uuid
from io import BytesIO
from os.path import splitext
from hashlib import sha256

import os

import docx2txt
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.core.validators import FileExtensionValidator
from django.db import models
from django.conf import settings
import iscc
from martor.models import MartorField

from telegramtoken.utils import get_client
from telegramtoken.validators import validate_address

from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)


class UserManager(BaseUserManager):
    def create_user(self, email, password=None):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_staffuser(self, email, password):
        """
        Creates and saves a staff user with the given email and password.
        """
        user = self.create_user(
            email,
            password=password,
        )
        user.staff = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        """
        Creates and saves a superuser with the given email and password.
        """
        user = self.create_user(
            email,
            password=password,
        )
        user.staff = True
        user.admin = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )
    active = models.BooleanField(default=True)
    staff = models.BooleanField(default=False) # a admin user; non super-user
    admin = models.BooleanField(default=False) # a superuser
    # notice the absence of a "Password field", that's built in.

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [] # Email & Password are required by default.
    objects = UserManager()

    def get_full_name(self):
        # The user is identified by their email address
        return self.email

    def get_short_name(self):
        # The user is identified by their email address
        return self.email

    def __str__(self):              # __unicode__ on Python 2
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        return self.staff

    @property
    def is_admin(self):
        "Is the user a admin member?"
        return self.admin

    @property
    def is_active(self):
        "Is the user active?"
        return self.active



class WalletID(models.Model):

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        help_text='Owner of Wallet-ID',
        on_delete=models.CASCADE,
    )

    address = models.CharField(
        verbose_name='Wallet-ID',
        help_text='A valid blockchain wallet address.',
        max_length=60,
    )

    memo = models.CharField(
        max_length=255,
        verbose_name='Internal Memo',
        help_text='Short internal note about this address.',
        blank=True
    )

    class Meta:
        verbose_name = 'Wallet-ID'
        verbose_name_plural = 'Wallet-IDs'

    def __str__(self):
        return '{} - {}'.format(self.owner, self.address)

class TelegramContent(models.Model):

    IMAGE_EXTENSIONS = ('jpg', 'png',)
    TEXT_EXTENSIONS = ('txt', 'docx')
    ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS + TEXT_EXTENSIONS

    ident = models.CharField(
        verbose_name='ISCC',
        max_length=55,
        blank=True,
    )

    title = models.CharField(
        verbose_name='Content Title',
        max_length=128,
        blank=False,
    )

    extra = models.CharField(
        verbose_name='Extra Info',
        max_length=128,
        blank=True,
        default="",
    )

    file = models.FileField(
        verbose_name='Telegram Content File',
        help_text='Supported file types: {}'.format(ALLOWED_EXTENSIONS),
        upload_to='mediafiles',
        blank=False,
        validators=[
            FileExtensionValidator(allowed_extensions=ALLOWED_EXTENSIONS),
        ],
    )

    name = models.CharField(
        verbose_name='Filename',
        max_length=255,
    )

    tophash = models.CharField(
        verbose_name='tophash',
        max_length=64,
        blank=True,
        default=''
    )

    txid = models.CharField(
        verbose_name='Transaction-ID',
        help_text='Blockchain TX-ID of registered ISCC',
        max_length=64,
        blank=True,
        default=''
    )

    class Meta:
        verbose_name = 'Telegram Content'
        verbose_name_plural = 'Telegram Contents'

    def __str__(self):
        return self.title

    def natural_key(self):
        return str(self)

    def register(self):
        # Register ISCC
        data = {
            'json': {
                'title': self.title,
                'tophash': self.tophash,
            }
        }
        if self.extra:
            data['json']['extra'] = self.extra

        client = get_client()
        txid = client.publish(
            settings.STREAM_ISCC,
            key_or_keys=list(self.ident.split('-')),
            data_hex_or_data_obj=data
        )
        return txid

    def clean(self):
        super().clean()
        if self.txid:
            raise ValidationError('Cannot change registered entry')
        if not self.pk and self.file:
            if not self.file.name.lower().endswith(self.ALLOWED_EXTENSIONS):
                raise ValidationError('Please provide a supported format: {}'.format(
                    self.ALLOWED_EXTENSIONS))
            basename, ext = os.path.splitext(self.file.name)
            # Store original file name
            self.name = self.file.name
            # Save with sanitized uuid as filename
            self.file.name = u''.join([str(uuid.uuid4()), ext.lower()])

    def save(self, *args, **kwargs):
        mid, title, extra = iscc.meta_id(self.title, self.extra)
        if self.ident:
            new_ident = [mid] + list(self.ident.split('-')[1:])
            self.ident = '-'.join(new_ident)
        if self.file:
            new_upload = isinstance(self.file.file, UploadedFile)
            if new_upload:
                # Generate ISCC

                filename, file_extension = splitext(self.file.name)
                ext = file_extension.lower().lstrip('.')
                data = self.file.open('rb').read()
                if ext in self.TEXT_EXTENSIONS:
                    if ext == 'docx':
                        text = docx2txt.process(BytesIO(data))
                        print(text)
                    else:
                        text = self.file.open().read()
                    cid = iscc.content_id_text(text)
                elif ext in self.IMAGE_EXTENSIONS:
                    cid = iscc.content_id_image(BytesIO(data))
                did = iscc.data_id(data)
                iid, self.tophash = iscc.instance_id(data)
                iscc_code = '-'.join((mid, cid, did, iid))
                self.ident = iscc_code
        super(TelegramContent, self).save(*args, **kwargs)


class ActivationMode(models.Model):

    PAYMENT = 'PAYMENT'
    TOKEN = 'TOKEN'

    ACTIVATION_MODES = (
        (PAYMENT, 'On-chain Payment'),
        (TOKEN, 'On-chain Tokenization'),
    )

    ident = models.CharField(primary_key=True, choices=ACTIVATION_MODES, max_length=24)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Transaction Model'
        verbose_name_plural = 'Transaction Models'

    def __str__(self):
        return self.ident

class TelegramQuerySet(models.QuerySet):

    def tokenized(self):
        return self.filter(transaction_model=ActivationMode.TOKEN)

    def payable(self):
        return self.filter(transaction_model=ActivationMode.PAYMENT)



class TelegramToken(models.Model):

    ident = models.UUIDField(
        verbose_name='Telegram token ID',
        help_text='Identifier of this specific TelegramToken offer',
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    info = models.CharField(
        verbose_name='Public Info',
        help_text='A short public description about the Telegram token. '
                  'Will also be added as info to tokens.',
        max_length=255,
        blank=False
    )

    administrator = models.ForeignKey(
        'telegramtoken.WalletID',
        verbose_name='Administrator wallet ID',
        help_text='Wallet-ID of Administrator. By default the stream '
                  'publisher Wallet-ID is assumed to be the '
                  'licensor. This assumption can be overridden by '
                  'providing an explicit list of one or more Wallet-IDs. '
                  'Future extensibility: licensor_identifier_type.',
        on_delete=models.CASCADE
  )
    organization = models.ForeignKey(
        'organizations.organizationuser',
        verbose_name='Telegram Organization',
        help_text='Organization assigned to this Telegram Token',
        on_delete=models.CASCADE
    )
    material = models.ForeignKey(
        'telegramtoken.TelegramContent',
        verbose_name='Telegram Content',
        help_text='The contract materials for this TelegramToken',
        related_name='material_telegramtokens',
        on_delete=models.CASCADE
    )

    transaction_model = models.ForeignKey(
        'telegramtoken.ActivationMode',
        verbose_name='Transaction Model',
        help_text='Transaction Model accepted by the TelegramToken. If no '
                  'Transaction Model is given the TelegramToken is purely '
                  'informational and there is no defined way to close a '
                  'license contract on-chain.',
        related_name='+',
        blank=True,
        on_delete=models.CASCADE
    )

    txid = models.CharField(
        verbose_name='Transaction-ID',
        help_text='Blockchain TX-ID of published Telegram token',
        max_length=64,
        blank=True,
        default=''
    )

    objects = TelegramQuerySet.as_manager()

    class Meta:
        verbose_name = "Telegram token"
        verbose_name_plural = "Telegram token"

    def __str__(self):
        return self.info

    def get_absolute_url(self):
        return '/telegramtoken/%s/' % self.ident

    def to_primitive(self):
        """Return python dict for stream publishing"""
        data = dict(
           transaction_models=[self.transaction_model.ident],
        )
        wrapped = {'json': data}
        return wrapped

    def register(self, save=False):
        client = get_client()
        keys = [str(self.ident), self.material.ident]
        txid = client.publishfrom(
            self.administrator.address,
            settings.STREAM_TELEGRAM,
            keys, self.to_primitive()
                   )

        # Create token if tokenize transaction model
        if self.transaction_model.ident == ActivationMode.TOKEN:
            client.issue(
                address=self.administrator.address,
                asset_name_or_asset_params={
                    'name': self.ident.bytes.hex(),
                    'open': True
                },
                quantity=1000,
                smallest_unit=1,
                native_amount=0.1,
                custom_fields={
                    'info': self.info,
                    'type': 'telegram-token'
                }
            )
        if save:
            self.txid = txid
            self.save()
        return txid


class TelegramTransaction(models.Model):

    telegram_token = models.ForeignKey(
        TelegramToken,
        verbose_name='Telegram token',
        help_text='Choose Telegram token for which you want to send a Token',
        on_delete=models.CASCADE
    )

    recipient = models.CharField(
        verbose_name='Recipient',
        help_text='Walled-ID of user to whom you want to send the Telegram token Token',
        max_length=64,
        validators=[validate_address]
    )

    txid = models.CharField(
        verbose_name='Transaction-ID',
        help_text='Blockchain TX-ID of token transaction',
        max_length=64,
        blank=True,
        default=''
    )

    class Meta:
        verbose_name = 'Token Transaction'
        verbose_name_plural = 'Token Transactions'

    def register(self):
        client = get_client()
        token_name = self.telegram_token.ident.bytes.hex()
        txid = client.sendasset(
            address=self.recipient,
            asset_identifier=token_name,
            asset_qty=1,
            native_amount=0.1
        )
        return txid

    def save(self, *args, **kwargs):
        if not self.txid:
            self.txid = self.register()
        super(TokenTransaction, self).save(*args, **kwargs)
