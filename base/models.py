from django.db import models
from django.contrib.auth import get_user_model
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
    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
    authors = models.ManyToManyField(get_user_model(), related_name="pub_authored", blank=True)
    theme = models.CharField(max_length=400)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="publications")
    affiliations = models.TextField(
        blank=True,
        null=True,
        help_text="Enter affiliations separated by commas (,)"
    )
    file = models.FileField(upload_to=utils.pdfUploadPath, validators=[utils.validatePdf])
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

    

class Message(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
    body = models.TextField()
    updated = models.DateTimeField(auto_now=True) 
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updated', '-created']

    def __str__(self):
        return self.body[0:50]