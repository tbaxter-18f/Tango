import os

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.html import strip_tags

from tango_shared.maptools import get_geocode

THEME_CHOICES = [(theme, theme.capitalize()) for theme in settings.ALLOWABLE_THEMES]


class Profile(AbstractUser):
    """
    Subclasses AbstractUser to provide site-specific user fields.
    """
    preferred_name = models.CharField('Display name', max_length=200, blank=True, null=True, help_text="If you would prefer a different screen name, enter it here. Spaces are allowed. Note: your username will not change.")
    street_address = models.CharField(max_length=255, blank=True, help_text="Will never be shown publicly on the site.")
    city           = models.CharField(max_length=200, blank=True)
    state          = models.CharField(max_length=200, blank=True)
    country        = models.CharField(max_length=200, blank=True)
    zip            = models.CharField(max_length=10, blank=True, help_text="Will never be shown publicly on the site.")
    interests      = models.CharField(max_length=200, blank=True)
    occupation     = models.CharField(max_length=200, blank=True)
    birthday       = models.DateField(blank=True, null=True)
    homepage       = models.URLField('Your web site', blank=True)
    bio            = models.TextField(help_text='Tell us a bit about yourself.', blank=True, null=True)
    signature      = models.CharField(max_length=255, blank=True, help_text="You can have a short signature line on the board. Members who choose to view signatures can see it. HTML is not allowed.")
    post_count     = models.IntegerField(default="0", editable=False)
    geocode        = models.CharField(max_length=200, null=True, blank=True)
    avatar         = models.ImageField(blank=True, null=True)

    #preferences
    display_on_map = models.BooleanField(default=True)
    open_links = models.BooleanField("Open links in new window", default=False, help_text="Check if you would like links to automatically open in a new window.")
    show_signatures  = models.BooleanField(default=False, help_text="Check if you would like to see signatures attached to forum posts.")
    #collapse_header  = models.BooleanField(default=False, help_text="Check if you would like the site header collapsed by default. Note that you may miss important information.")
    #theme            = models.CharField(max_length=100, blank=True, choices=THEME_CHOICES)
    #auto_load_forum  = models.BooleanField('Auto-load forum pages', default=True, help_text="If checked, forum topics will load automatically, so you don't have to click to go to the next page. Note: auto-loading is disabled on mobile devices.")
    #get_digest       = models.BooleanField('Get daily email', default=False, help_text="If checked, you'll get a once-a-day email notifying you of new site activity. You can change this setting whenever you like.")

    class Meta:
        ordering = ('preferred_name',)

    def __unicode__(self):
        return self.username

    def save(self, *args, **kwargs):
        needs_geocode = False
        if self.id is None:  # For new user, only set a few things:
            self.preferred_name = self.get_display_name()
            needs_geocode = True
        else:
            old_self = self.__class__.objects.get(id = self.id)
            if old_self.city != self.city or old_self.state != self.state or self.geocode is None:
                needs_geocode = True
            if old_self.preferred_name != self.preferred_name or old_self.first_name != self.first_name or old_self.last_name != self.last_name:
                self.preferred_name = self.get_display_name()  # check if preferred name has changed
            if old_self.avatar and old_self.avatar != self.avatar:
                os.remove(old_self.avatar.path)
        if self.city and self.state and needs_geocode:
            geocode = get_geocode(self.city, self.state, street_address=self.street_address, zipcode=self.zip)
            if geocode and geocode != '620':
                self.geocode = ', '.join(geocode)
        if self.signature:
            self.signature = strip_tags(self.signature)

        super(Profile, self).save(*args, **kwargs)

    # fix this for current URL -- use permalink
    def get_absolute_url(self):
        return reverse('view_profile', args=[self.username])

    def get_display_name(self):
        """
        Determined preferred screen name based on the first of
        preferred_name, full name, or username.
        """
        if self.preferred_name:
            return self.preferred_name
        elif self.first_name and self.last_name:
            return '{0} {1}'.format(self.first_name, self.last_name)
        else:
            return self.username