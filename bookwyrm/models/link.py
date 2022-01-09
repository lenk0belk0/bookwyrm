""" outlink data """
from urllib.parse import urlparse

from django.db import models
from django.utils.translation import gettext_lazy as _

from bookwyrm import activitypub
from .activitypub_mixin import ActivitypubMixin
from .base_model import BookWyrmModel
from . import fields


class Link(ActivitypubMixin, BookWyrmModel):
    """a link to a website"""

    url = fields.URLField(max_length=255, activitypub_field="href")
    domain = models.ForeignKey(
        "LinkDomain", on_delete=models.PROTECT, null=True, blank=True
    )

    activity_serializer = activitypub.Link
    reverse_unfurl = True

    @property
    def name(self):
        """link name via the assocaited domain"""
        return self.domain.name

    def save(self, *args, **kwargs):
        """create a link"""
        # get or create the associated domain
        if not self.domain:
            domain = urlparse(self.url).netloc
            self.domain, _ = LinkDomain.objects.get_or_create(domain=domain)

        # this is never broadcast, the owning model broadcasts an update
        if "broadcast" in kwargs:
            del kwargs["broadcast"]
        return super().save(*args, **kwargs)


class FileLink(Link):
    """a link to a file"""

    book = models.ForeignKey(
        "Book", on_delete=models.CASCADE, related_name="file_links", null=True
    )
    filetype = fields.CharField(max_length=5, activitypub_field="mediaType")


StatusChoices = [
    ("approved", _("Approved")),
    ("blocked", _("Blocked")),
    ("pending", _("Pending")),
]


class LinkDomain(BookWyrmModel):
    """List of domains used in links"""

    domain = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=50, choices=StatusChoices, default="pending")
    name = models.CharField(max_length=100)

    def save(self, *args, **kwargs):
        """set a default name"""
        if not self.name:
            self.name = self.domain
        super().save(*args, **kwargs)