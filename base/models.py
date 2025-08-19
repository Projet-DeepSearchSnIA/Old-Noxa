from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.auth import get_user_model
from django.utils import timezone
from . import utils

from PyPDF2 import PdfReader


class Topic(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class Tag(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Publication(models.Model):
    user = models.ForeignKey(
        get_user_model(), 
        on_delete=models.SET_NULL, 
        null=True)
    authors = models.ManyToManyField(
        get_user_model(), 
        related_name="pub_authored", 
        blank=True)
    theme = models.CharField(max_length=400)
    topic = models.ForeignKey(Topic, 
                              on_delete=models.SET_NULL, 
                              null=True
                              )
    tags = models.ManyToManyField(
        Tag, 
        blank=True, 
        related_name="publications"
    )
    affiliations = models.TextField(
        blank=True,
        null=True,
        help_text="Enter affiliations separated by commas (,)"
    )
    file = models.FileField(
        upload_to=utils.pdfUploadPath, 
        validators=[utils.validatePdf]
    )
    # title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated', '-created']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # sauvegarde d'abord l'objet
        if self.user and self.user not in self.authors.all():
            self.authors.add(self.user)

    def get_affiliations_list(self):
        """Return affiliations as a list."""
        return [aff.strip() for aff in self.affiliations.split(",") if aff.strip()]
    
    def page_count(self):
        try:
            self.file.open('rb')
            reader = PdfReader(self.file)
            return len(reader.pages)
        except:
            return None
        finally:
            self.file.close()

    def __str__(self):
        return self.theme
    

class Collection(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    publications = models.ManyToManyField(
        'Publication',
        through='CollectionPublication',
        related_name='collections',
        blank=True
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    

class CollectionPublication(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
    added = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('collection', 'publication')  # prevent duplicates
        ordering = ['-added']

    def __str__(self):
        return f"{self.publication} in {self.collection} (added {self.added})"


class Notification(models.Model):
    """
    Notification class: inherits from django.db.models.Model \n
    Properties:\n
    recipient: who receives the notification \n
    actor: who triggered the notification \n
    type: type of notification (follow, discussion in publication, ...). Default value set in NOTIFICATION_TYPES \n
    target: the object this notification is about, depends on the notification's type. 
    For follow notification, the target is the follower, for discussion in publication notification, the target is the discussion itself\n
    title: notification title\n
    message: the body of the notification\n
    is_read: read status\n
    is_deleted: deleted status, when deleted stays in database but doesn't show up in notification ever again\n
    created: date of creation\n
    read_at: read date\n
    action_url: for redirecting to the target object page
    Methods:\n
    mark_as_read: marks the notification as read
    """

    NOTIFICATION_TYPES = [
        ('follow', 'New Follower'),
        ('discussion_in_publication', 'New discussion in publication'),
        # ('follow_accepted', 'Follow Request Accepted'),
        ('publication_like', 'Publication Liked'),
        ('publication_comment', 'New Comment on Publication'),
        ('collection_shared', 'Collection Shared'),
        ('discussion_reply', 'Discussion Reply'),
        ('discussion_mention', 'Mentioned in Discussion'),
        ('publication_added', 'New Publication from Followed User'),
        ('topic_follow', 'Someone Followed Your Topic'),
        ('system', 'System Notification'),
        ('achievement', 'Achievement Unlocked'),
    ] # not exhaustive list, just built it up quickly like that

    # Who receives the notification
    recipient = models.ForeignKey(
        get_user_model(), 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    
    # Who triggered the notification
    actor = models.ForeignKey(
        get_user_model(), 
        on_delete=models.CASCADE, 
        related_name='sent_notifications',
        null=True, 
        blank=True
    )
    
    # Type of notification
    type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    
    # The object this notification is about (publication, comment, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    target = GenericForeignKey('content_type', 'object_id')
    
    # Notification content
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Status
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    
    # Timestamps
    created = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Optional: Action URL for clicking the notification
    action_url = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['recipient', '-created']),
            models.Index(fields=['recipient', 'is_read']),
        ]

    def __str__(self):
        return f"{self.get_type_display()} for {self.recipient.username}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    @property
    def time_since(self):
        from django.utils.timesince import timesince
        return timesince(self.created)

# class Notification(models.Model):
#     user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
#     type = models.CharField(max_length=50)
#     body = models.TextField()
#     created = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         ordering = ['-created']

#     def __str__(self):
#         return f"{self.type} - {self.body} (added {self.created})"


class Discussion(models.Model):
    """
    Discussion class: inherits from django.db.models.Model \n
    Properties:\n
    creator: the user which created the room (automatically filled in, current logged in user)\n
    publication: which publication is this room about ? (automatically filled in)\n
    title: Discussion room name\n
    description: Small description of the discussion room, what point will this discussion talk about specifically or something else\n
    participants: people who wrote a message in this at least one time (will be incrementedly increased as people participate in it)\n
    updated: date of the last message (automatically filled in)\n
    created: date of creation (automatically filled in)
    """
    creator = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    participants = models.ManyToManyField(get_user_model(), related_name="participants", blank=True)
    updated = models.DateTimeField(auto_now=True) 
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updated', '-created']

    def __str__(self):
        return self.title
    

class Message(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    discussion = models.ForeignKey(Discussion, on_delete=models.CASCADE)
    body = models.TextField()
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    updated = models.DateTimeField(auto_now=True) 
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updated', '-created']

    def __str__(self):
        return self.body[0:50]
    
    @property
    def is_reply(self):
        """Check if this message is a reply to another message"""
        return self.reply_to is not None
    
    def get_replies(self):
        """Get all replies to this message"""
        return self.replies.all().order_by('created')