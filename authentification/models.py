from django.db import models
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify

class User(AbstractUser):
    photo = models.ImageField(upload_to='profils/', default='profils/default_profile.jpeg')
    school = models.CharField(max_length=100, default='ENSAE Dakar')
    bio = models.TextField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    github = models.URLField(blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True, null=True)
    nb_documents = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['username'] # Ensure users are ordered by username by default
        indexes = [
            models.Index(fields=['username']), # Index for faster lookups by username
            models.Index(fields=['email']), # Index for faster lookups by email
        ]
        constraints = [
            models.UniqueConstraint(fields=['email'], name='unique_email'), # Ensure emails are unique
        ]
        permissions = [
            ('can_view_user', 'Can view user'),
            ('can_edit_user', 'Can edit user'),
            ('can_delete_user', 'Can delete user'),
            ('can_add_document', 'Can add document'),
            ('can_view_document', 'Can view document'),
            ('can_edit_document', 'Can edit document'),
            ('can_delete_document', 'Can delete document'),
        ]
    
    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.username)
            slug = base_slug
            # Ensure slug is unique
            n = 1
            while User.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def add_document(self):
        """
        Increment the number of documents for the user.
        """
        self.nb_documents += 1
        self.save()
    
    
       
