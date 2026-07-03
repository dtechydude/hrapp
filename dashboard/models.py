from django.db import models
from django.db.models.signals import post_save, post_delete
from datetime import timedelta
from django.template.defaultfilters import slugify
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.urls import reverse
import os
from django.db.models import Q
from django.utils.html import strip_tags
from django_ckeditor_5.fields import CKEditor5Field
from embed_video.fields import EmbedVideoField
from django.core.exceptions import ValidationError
from djrichtextfield.models import RichTextField
# from portal.models import Dept

from tinymce.models import HTMLField


# New School Identity
class CorporateIdentity(models.Model):
    name = models.CharField(max_length=50)
    identity_label = models.CharField(max_length=50, help_text="e.g. Primary, Secondary, or Main", blank=True, null=True)
    is_default = models.BooleanField(default=False, help_text="Fallback identity if no specific class identity is set.")
    # ... (your existing address, phone, logo, signature fields) ...
    address = models.CharField(max_length=60)
    address_line_2 = models.CharField(max_length=250, blank=True, null=True)
    phone1 = models.CharField(max_length=11)
    phone2 = models.CharField(max_length=11, blank=True, null=True)
    email = models.CharField(max_length=50, blank=True, null=True)
    website = models.CharField(max_length=50, blank=True, null=True)
    logo = models.ImageField(default='school_logo.jpg', upload_to='official_pics', help_text='must not exceed 180px by 180px in size')
    signature = models.ImageField(blank=True, null=True, upload_to='official_pics', help_text='must not exceed 180px by 180px in size')

    slug = models.SlugField(null=True, blank=True)


    def save(self, *args, **kwargs):
        # Limit to 3 entries
        if not self.pk and CorporateIdentity.objects.count() >= 10:
            raise ValidationError(" Portal only supports up to 10 Corporate Identities.")
        
        # Ensure only one is the default
        if self.is_default:
            CorporateIdentity.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
            
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Corporate Identity Setting"
        verbose_name_plural = "Corporate Identity Settings"

    def __str__(self):
        return f"{self.name} ({self.identity_label})"


# Standard or another branch identity
class BranchIdentity(models.Model):
    # Link to your existing Standard/Class model
    branch = models.OneToOneField('Branch', on_delete=models.CASCADE, related_name='identity_mapping')
    # Link to one of the 3 identities
    corporate_identity = models.ForeignKey(CorporateIdentity, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Branch-Identity Mapping"
        verbose_name_plural = "Branch-Identity Mappings"

    def __str__(self):
        return f"{self.branch.name} -> {self.corporate_identity.identity_label}"



class Branch(models.Model):   
    name = models.CharField(max_length=100, unique=True)
    branch_manager = models.ForeignKey(
        'employees.Staff',  # Use 'app_name.ModelName'
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='branch_manager'
    )   
    promotion_order = models.IntegerField(unique=True, null=True, blank=True, help_text="Order of Branch )")
    desc = models.CharField(max_length=200, blank=True, null=True, verbose_name='description') 
    slug = models.SlugField(null=True, blank=True)


    class Meta:
        verbose_name = 'Branch'
        verbose_name_plural = 'Branch'
        # ordering =['promotion_order']

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

