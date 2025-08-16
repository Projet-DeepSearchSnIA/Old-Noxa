from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.db.models import Q
from django.utils.safestring import mark_safe
from django.db.models import Count

import os
import markdown

from .models import Topic, Tag, Publication, Message, Collection, CollectionPublication


def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    topics = Topic.objects.all()

    pubs = Publication.objects.filter(
        Q(theme__icontains = q) |
        Q(topic__name__icontains = q) |
        Q(tags__name__icontains = q)
    ).distinct()

    if request.user.is_authenticated:
        collections = (
            request.user.collection_set
            .annotate(pub_count=Count("publications"))
            .prefetch_related("publications")
        )
        # collections = request.user.collection_set.all()
    else:
        collections = None

    context = {'topics': topics, 'pubs': pubs, "collections": collections}

    return render(request, "base/home.html", context)

def publication(request, pk: str):
    pub = Publication.objects.get(id = pk)

    pub.summary_html = mark_safe(markdown.markdown(pub.summary))

    similar_pubs = Publication.objects.filter(
        Q(topic=pub.topic) | Q(tags__in=pub.tags.all())
    ).exclude(id=pub.id).distinct()

    if request.user.is_authenticated:
        collections = request.user.collection_set.all()
    else:
        collections = None

    context = {'pub': pub, 'similar_pubs': similar_pubs, "collections": collections}

    return render(request, "base/publication.html", context)

def filterTopics(request):
    query = request.GET.get("q", "") # Ajax queue

    topics = Topic.objects.filter(name__icontains=query)[:10]
    results = [{"id": t.id, "text": t.name} for t in topics]
    return JsonResponse({"results": results})

def filterAuthors(request):
    query = request.GET.get("q", "")
    
    authors = get_user_model().objects.filter(username__icontains=query)[:10]
    results = [{"id": a.id, "text": a.username} for a in authors]
    return JsonResponse({"results": results})

def filterTags(request):
    query = request.GET.get("q", "")
    
    tags = Tag.objects.filter(name__icontains=query)[:10]
    results = [{"id": t.id, "text": t.name} for t in tags]
    return JsonResponse({"results": results})

@login_required
def createPublication(request):
    if request.method == 'POST':
        # Get form data
        theme = request.POST.get('theme')
        topic_name = request.POST.get('topic')
        affiliations = request.POST.get('affiliations')
        description = request.POST.get('description')
        summary = request.POST.get('summary')
        authors_str = request.POST.get('authors', '')
        tags_str = request.POST.get('tags', '')
        file = request.FILES.get('file')
        
        # Handle topic
        topic, _ = Topic.objects.get_or_create(name=topic_name)
        
        # Create publication
        publication = Publication.objects.create(
            theme=theme,
            topic=topic,
            affiliations = affiliations,
            description=description,
            summary=summary,
            file=file,
            user=request.user  # assuming current user is main author
        )
        
        # Handle additional authors
        if authors_str:
            author_usernames = [username.strip() for username in authors_str.split(',') if username.strip()]
            for username in author_usernames:
                try:
                    author = get_user_model().objects.get(username=username)
                    publication.authors.add(author)  # assuming ManyToMany field
                except get_user_model().DoesNotExist:
                    pass  # Skip if author doesn't exist
        
        # Handle tags
        if tags_str:
            tag_names = [tag_name.strip() for tag_name in tags_str.split(',') if tag_name.strip()]
            for tag_name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                publication.tags.add(tag)  # assuming ManyToMany field
        
        return redirect('base:publication', pk=publication.pk)
    
    # Handle GET request
    return render(request, 'base/publication_form.html')

# @login_required
# def createPublication(request):
#     users = get_user_model().objects.all()
#     topics = Topic.objects.all()
#     tags = Tag.objects.all()
#     if request.method == "POST":
#         form = PublicationForm(request.POST, request.FILES, user=request.user)
#         if form.is_valid():
#             publication = form.save(commit=False)
#             publication.user = request.user
#             publication.save()
            
#             # Save many-to-many relationships
#             form.save_m2m()
            
#             # Ensure the user is added as an author
#             if publication.user not in publication.authors.all():
#                 publication.authors.add(publication.user)
            
#             messages.success(request, 'Publication created successfully!')
#             return redirect('base:home')
#         else:
#             messages.error(request, 'Please correct the errors below.')
#     else:
#         form = PublicationForm(user=request.user)

#     context = {'form': form, 'users': users, 'topics': topics, 'tags': tags}
#     return render(request, "base/publication_form.html", context)

def viewPdf(request, pk: str):
    pub = get_object_or_404(Publication, id=pk)
    
    pdf_path = pub.file.path
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        raise Http404("PDF file not found")
    
    # Serve the PDF directly
    with open(pdf_path, 'rb') as pdf_file:
        response = HttpResponse(pdf_file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{pub.file.name}"'
        return response


@login_required
def userProfile(request, pk: str):
    User = get_user_model()
    user = User.objects.get(id = pk)

    pubs = Publication.objects.filter(
        authors__username = user.username
    )

    collections = (
        user.collection_set
        .annotate(pub_count=Count("publications"))
        .prefetch_related("publications")
    )

    context = {'pubs': pubs, 'user': user, 'collections': collections}

    return render(request, "base/profile.html", context)

def createCollection(request):
    if request.method == "POST":
        name = request.POST.get("name")
        if name:
            Collection.objects.create(user=request.user, name=name)
            messages.success(request, "Collection created successfully!")
        else:
            messages.error(request, "Name is required.")
    return redirect(request.META.get("HTTP_REFERER", "home"))

@login_required
def deleteCollection(request, pk: str):
    
    collection = get_object_or_404(Collection, id=pk)
    
    # Check permissions
    if collection.user != request.user:
        messages.error(request, 'Permission denied')
        return redirect(request.META.get('HTTP_REFERER', 'base:home'))
    
    # Remove collection
    collection_name = collection.name  # Store name before deletion for message
    collection.delete()
    messages.success(request, f'Collection "{collection_name}" deleted successfully')
    
    return redirect('base:user-profile', pk=request.user.id)


@login_required
def addToCollection(request, pk: str):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()

        if not name:
            messages.error(request, "Collection name is required.")
            return redirect(request.META.get("HTTP_REFERER", "home"))

        # Get or create the collection for the current user
        collection, created = Collection.objects.get_or_create(
            user=request.user,
            name=name
        )

        # Get the publication and add it to the collection
        pub = get_object_or_404(Publication, id=pk)
        collection.publications.add(pub)

        if created:
            messages.success(request, f'New collection "{name}" created and publication added!')
        else:
            messages.success(request, f'Publication added to collection "{name}".')

    return redirect(request.META.get("HTTP_REFERER", "home"))


def collection(request, pk_u: str, pk_c: str):
    collection = Collection.objects.get(id=pk_c)
    User = get_user_model()
    user = get_object_or_404(User, id=pk_u)
    collections = (
        user.collection_set
        .annotate(pub_count=Count("publications"))
        .prefetch_related("publications")
    )
    publications = CollectionPublication.objects.filter(collection=collection).select_related('publication')

    context = {'user': user, 'collection': collection, "publications": publications, "collections": collections}
    return render(request, "base/collection.html", context)


@login_required
def deleteFromCollection(request, collection_id, publication_id):
    collection = get_object_or_404(Collection, id=collection_id)
    publication = get_object_or_404(Publication, id=publication_id)
    
    # Check permissions
    if collection.user != request.user:
        messages.error(request, 'Permission denied')
        return redirect(request.META.get('HTTP_REFERER', 'base:home'))
    
    # Remove from collection
    collection_pub = CollectionPublication.objects.filter(
        collection=collection, 
        publication=publication
    ).first()
    
    if collection_pub:
        collection_pub.delete()
        messages.success(request, 'Publication removed from collection')
    
    return redirect(request.META.get('HTTP_REFERER', 'base:home'))


@login_required
def addTopicToFav(request, pk: str):
    topic = get_object_or_404(Topic, id=pk)
    
    # Check if already in favorites
    if request.user.favorite_topics.filter(id=topic.id).exists():
        messages.info(request, f'"{topic.name}" is already in your favorites')
    else:
        # Add topic to favorites
        request.user.favorite_topics.add(topic)
        messages.success(request, f'"{topic.name}" added to your favorites')
    
    return redirect(request.META.get('HTTP_REFERER', 'base:home'))

@login_required
def removeTopicFromFav(request, pk: str):
    topic = get_object_or_404(Topic, id=pk)
    
    request.user.favorite_topics.remove(topic)
    messages.success(request, f'"{topic.name}" removed from your favorites')
    
    return redirect(request.META.get('HTTP_REFERER', 'base:home'))







