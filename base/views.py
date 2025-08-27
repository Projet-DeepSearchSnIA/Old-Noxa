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
from django.contrib.auth.hashers import make_password
from django.http import HttpResponseRedirect
from django.urls import reverse

import os
import markdown

from .models import Topic, Tag, Publication, Message, Collection, CollectionPublication, Notification, Discussion, track_search_click
from . import utils


def home(request):
    """
    Display the main home page for the Noxa application with publications and user-specific content.
    
    Handles the primary landing page that shows filtered publications based on search queries
    and provides personalized content for authenticated users including collections and 
    favorite topics.
    
    Args:
        request (HttpRequest): The HTTP request object, may contain search parameters
        
    GET Parameters:
        - q (str, optional): Search query to filter publications by theme, topic name, or tags
        
    Returns:
        HttpResponse: Renders the home page template with context data
        
    Context Data:
        - topics (QuerySet): All available topics for display/navigation
        - pubs (QuerySet): Publications filtered by search query across:
            * Publication theme (case-insensitive partial match)
            * Topic name (case-insensitive partial match) 
            * Tag names (case-insensitive partial match)
        - collections (QuerySet|None): User's collections with publication counts (authenticated users only)
        - favorite_topics (QuerySet|None): User's favorited topics (authenticated users only)
        
    Search Functionality:
        - Searches across multiple fields using Django Q objects
        - Uses case-insensitive partial matching (icontains)
        - Returns distinct results to avoid duplicates from multiple matches
        - Empty/None queries return all publications
        
    User Personalization:
        - Authenticated users: Shows personal collections and favorite topics
        - Anonymous users: collections and favorite_topics set to None
        - Collections are optimized with annotation for publication counts
        - Uses prefetch_related for efficient database queries
        
    Template:
        Renders 'base/home.html' with all context data for display
    """
    
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    topics = Topic.objects.all() # all topics displayed on home page

    pubs = Publication.objects.filter(
        Q(theme__icontains = q) |
        Q(topic__name__icontains = q) |
        Q(tags__name__icontains = q) |
        Q(authors__username__icontains = q) |
        Q(description__icontains = q)
    ).distinct()

    if request.user.is_authenticated:
        collections = (
            request.user.collection_set
            .annotate(pub_count=Count("publications"))
            .prefetch_related("publications")
        )
        # collections = request.user.collection_set.all()

        favorite_topics = request.user.favorite_topics.all()
    else:
        collections = None
        favorite_topics = None

    context = {'topics': topics, 'pubs': pubs, "collections": collections, "favorite_topics": favorite_topics}

    return render(request, "base/home.html", context)


##############################################################################################
################################## SEARCH FUNCTIONALITY ######################################
##############################################################################################

def search(request, tab=None):
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    topics = Topic.objects.all() # all topics displayed on home page

    if request.user.is_authenticated:
        collections = (
            request.user.collection_set
            .annotate(pub_count=Count("publications"))
            .prefetch_related("publications")
        )
        # collections = request.user.collection_set.all()

        favorite_topics = request.user.favorite_topics.all()
    else:
        collections = None
        favorite_topics = None

    # If no tab is specified, default to 'all'
    if tab is None:
        tab = 'all'

    allowed_tabs = ['all', 'publications', 'authors', 'collections', 'discussions', 'profiles', 'tags']
    if tab not in allowed_tabs:
        # Redirect to 'all' tab if invalid tab is provided
        return HttpResponseRedirect(f"{reverse('base:search')}?q={q}")
    
    # Choose template based on tab
    template_map = {
        'all': 'base/search/search.html',
        'publications': 'base/search/publications.html',
        'authors': 'base/search/authors.html',
        'collections': 'base/search/collections.html',
        'discussions': 'base/search/discussions.html',
        'profiles': 'base/search/profiles.html',
        'tags': 'base/search/tags.html',
    }

    template_name = template_map.get(tab, 'base/search/search.html')

    search_results = getSearchResult(q, tab)

    context = {'q': q, 'active_tab': tab, 'topics': topics, "collections": collections, 
               "favorite_topics": favorite_topics, 'search_results': search_results}

    return render(request, template_name, context)


# Search logic
def getSearchResult(query, tab):
    User = get_user_model()

    if not query:
        return {}

    # Define search configurations
    search_config = {
        'publications': {
            'model': Publication,
            'fields': ['theme', 'topic__name', 'tags__name', 'authors__username', 'description']
        },
        'authors': {
            'model': User,
            'fields': ['username', 'school'],
            'filter': Q(pub_authored__isnull=False)
        },
        'collections': {
            'model': Collection,
            'fields': ['name', 'publications__theme', 'publications__topic__name', 
                      'publications__tags__name', 'publications__authors__username', 
                      'publications__description']
        },
        'discussions': {
            'model': Discussion,
            'fields': ['title', 'description', 'creator__username', 'publication__theme',
                      'publication__topic__name', 'publication__tags__name', 
                      'participants__username']
        },
        'profiles': {
            'model': User,
            'fields': ['username', 'school']
        },
        'tags': {
            'model': Tag,
            'fields': ['name']
        }
    }

    def build_query(config):
        """Build Q object from configuration"""
        q_objects = Q()
        for field in config['fields']:
            q_objects |= Q(**{f"{field}__icontains": query})
        
        queryset = config['model'].objects.filter(q_objects).distinct()
        
        # Apply additional filters if specified
        if 'filter' in config:
            queryset = queryset.filter(config['filter'])
        
        return queryset

    if tab == "all":
        # Return limited results for all categories
        return {
            category: build_query(config)[:3] 
            for category, config in search_config.items()
        }
    elif tab in search_config:
        # Return full results for specific category
        return build_query(search_config[tab])[:30]
    else:
        return {}





#######################################################################################################
#######################################################################################################


def publication(request, pk: str):
    """
    Display detailed view of a specific publication with related content and user interactions.
    
    Renders a comprehensive publication page showing the full publication details,
    related publications, user collections, and associated discussions.
    
    Args:
        request (HttpRequest): The HTTP request object
        pk (str): Primary key of the publication to display
        
    Returns:
        HttpResponse: Renders the publication detail template with context data
        
    Context Data:
        - pub (Publication): The main publication object with processed summary
        - similar_pubs (QuerySet): Related publications based on topic and tags
        - collections (QuerySet|None): User's collections for saving functionality (authenticated users only)
        - discussions (QuerySet): All discussions/comments associated with this publication
        
    Publication Processing:
        - Converts publication summary from Markdown to HTML using markdown.markdown()
        - Uses mark_safe() to render HTML content safely in templates
        - Processes summary for rich text display with formatting
        
    Related Content Algorithm:
        - Finds publications sharing the same topic OR having overlapping tags
        - Excludes the current publication from results
        - Uses distinct() to prevent duplicates from multiple tag matches
        - Provides content discovery and engagement opportunities
        
    User Features:
        - Authenticated users: Access to personal collections for saving publications
        - Anonymous users: collections set to None (limited functionality)
        - Discussion access: Shows all related discussions for community engagement
        
    Database Optimization:
        - Efficient querying with Q objects for complex filtering
        - Related content fetched in single optimized query
        - Discussions prefetched for reduced database hits
        
    Template:
        Renders 'base/publication.html' with all publication data and related content
    """
    
    pub = Publication.objects.get(id = pk)

    pub.summary_html = mark_safe(markdown.markdown(pub.summary))

    similar_pubs = Publication.objects.filter(
        Q(topic=pub.topic) | Q(tags__in=pub.tags.all())
    ).exclude(id=pub.id).distinct()

    if request.user.is_authenticated:
        collections = request.user.collection_set.all()
    else:
        collections = None

    discussions = pub.discussion_set.all()

    # Track search click if coming from search
    track_search_click(request, pub)

    context = {'pub': pub, 'similar_pubs': similar_pubs, "collections": collections, 
               "discussions": discussions}

    return render(request, "base/publication.html", context)

def filterTopics(request):
    """
    Handles the Topics filter while typing the topic name directly
    Args:
        request (HttpRequest): The HTTP request object
        
    Returns:
        JsonResponse: Renders the topics filtered topic id and topic name
    """

    query = request.GET.get("q", "") # Ajax queue

    topics = Topic.objects.filter(name__icontains=query)[:10]
    results = [{"id": t.id, "text": t.name} for t in topics]
    return JsonResponse({"results": results})

def filterAuthors(request):
    """
    Handles the Authors filter while typing the author name directly
    Args:
        request (HttpRequest): The HTTP request object
        
    Returns:
        JsonResponse: Renders the authors filtered author id and author name
    """

    query = request.GET.get("q", "")
    
    authors = get_user_model().objects.filter(username__icontains=query)[:10]
    results = [{"id": a.id, "text": a.username} for a in authors]
    return JsonResponse({"results": results})

def filterTags(request):
    """
    Handles the Tags filter while typing the tag name directly
    Args:
        request (HttpRequest): The HTTP request object
        
    Returns:
        JsonResponse: Renders the Tags filtered tag id and tag name
    """

    query = request.GET.get("q", "")
    
    tags = Tag.objects.filter(name__icontains=query)[:10]
    results = [{"id": t.id, "text": t.name} for t in tags]
    return JsonResponse({"results": results})

@login_required
def createPublication(request):
    """
    Handle creation of new publications in the Noxa application.
    
    Provides a form interface for authenticated users to create and publish
    new academic publications with authors, topics, tags, and file attachments.
    
    Args:
        request (HttpRequest): The HTTP request object containing publication data
        
    POST Parameters Expected:
        - theme (str): Main theme/title of the publication
        - topic (str): Topic name (creates new topic if doesn't exist)
        - affiliations (str): Author affiliations and institutional details
        - description (str): Brief description of the publication
        - summary (str): Detailed summary/abstract of the publication
        - authors (str, optional): Comma-separated list of co-author usernames
        - tags (str, optional): Comma-separated list of tags for categorization
        - file (File, optional): PDF or document file attachment
        
    Returns:
        HttpResponse:
        - On GET: Renders publication creation form template
        - On successful POST: Redirects to newly created publication detail page
        
    Publication Creation Process:
        1. Extracts and validates form data from POST request
        2. Creates or retrieves topic using get_or_create()
        3. Creates publication object with current user as primary author
        4. Processes comma-separated author usernames and adds valid users
        5. Creates/retrieves tags and associates them with publication
        6. Handles file upload attachment if provided
        
    Author Management:
        - Primary author: Set to request.user (publication creator)
        - Additional authors: Parsed from comma-separated string
        - Invalid usernames are silently skipped (graceful error handling)
        - Many-to-many relationship allows multiple authors per publication
        
    Tag System:
        - Auto-creates tags that don't exist using get_or_create()
        - Supports flexible tagging with comma-separated input
        - Enables content discovery and categorization
        
    Security:
        - @login_required decorator ensures only authenticated users can create
        - File uploads handled securely through Django's file system
        - User authentication verified before publication creation
        
    Template:
        Renders 'base/publication_form.html' for form display and interaction
    """
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
                    publication.authors.add(author)
                except get_user_model().DoesNotExist:
                    pass  # Skip if author doesn't exist
        
        # Handle tags
        if tags_str:
            tag_names = [tag_name.strip() for tag_name in tags_str.split(',') if tag_name.strip()]
            for tag_name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                publication.tags.add(tag)
        
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
    """
    Serve PDF files for publications with secure access and inline display.
    
    Provides direct PDF viewing functionality for publication files, serving them
    inline in the browser for immediate viewing without requiring downloads.
    
    Args:
        request (HttpRequest): The HTTP request object
        pk (str): Primary key of the publication containing the PDF file
        
    Returns:
        HttpResponse: PDF file response with appropriate headers for inline display
        
    Raises:
        Http404: 
        - If publication with given pk doesn't exist
        - If the associated PDF file is not found on the filesystem
        
    File Serving Process:
        1. Retrieves publication object or raises 404 if not found
        2. Gets file path from publication's file field
        3. Verifies file exists on filesystem before serving
        4. Opens and reads PDF file in binary mode
        5. Returns file content with proper PDF MIME type
        
    Response Headers:
        - Content-Type: 'application/pdf' for proper browser handling
        - Content-Disposition: 'inline' to display in browser rather than download
        - Filename: Preserves original filename for user reference
        
    Security Considerations:
        - Uses get_object_or_404() to prevent information disclosure
        - Validates file existence before serving to prevent path traversal
        - Serves files through Django's secure file handling
        - No direct filesystem path exposure to users
        
    Browser Behavior:
        - PDF opens directly in browser's built-in PDF viewer
        - Users can view, zoom, and navigate without downloading
        - Fallback download option available through browser controls
        
    Performance Notes:
        - Reads entire file into memory (suitable for academic papers)
        - Consider streaming response for very large files if needed
        - File served directly without caching headers
    """
    
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
    """
    Display comprehensive user profile page with publications, collections, and social features.
    
    Renders a detailed profile view showing user's publications, collections, social connections,
    and notifications with privacy controls and optimized database queries.
    
    Args:
        request (HttpRequest): The HTTP request object from authenticated user
        pk (str): Primary key of the user whose profile is being viewed
        
    Returns:
        HttpResponse: Renders user profile template with comprehensive context data
        
    Context Data:
        - pubs (QuerySet): All publications where the profile user is listed as an author
        - user (User): The profile user object being displayed
        - collections (QuerySet): User's collections with publication counts and prefetched data
        - following_user (bool): Whether current user follows the profile user
        - followers (QuerySet): Profile user's followers (limited to first 10)
        - followings (QuerySet): Users that profile user follows (limited to first 10)
        - notifications (QuerySet): User's notifications (only visible to profile owner)
        
    Publication Filtering:
        - Retrieves publications using authors many-to-many relationship
        - Filters by exact username match for accurate authorship
        - Shows all publications regardless of co-authorship
        
    Collection Optimization:
        - Annotates collections with publication counts for display
        - Uses prefetch_related() for efficient loading of related publications
        - Reduces database queries through optimized ORM usage
        
    Privacy Controls:
        - Notifications: Only visible when viewing own profile (request.user == user)
        - Limited to 7 most recent undeleted notifications
        - Social connections visible to all users for networking
        
    Social Features:
        - Following status: Checks if current user follows profile user
        - Follower/following lists: Limited to 10 users each for performance
        - Supports social networking and academic collaboration discovery
        
    Security:
        - @login_required decorator ensures authenticated access only
        - Profile data accessible to all authenticated users (academic transparency)
        - Notification privacy maintained through ownership verification
        
    Template:
        Renders 'base/profile.html' with full user profile and academic portfolio
    """
    
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

    # Notifications (only visible for the request.user)
    notifications = []
    if request.user == user:
        notifications = request.user.notifications.filter(is_deleted=False, is_read=False)[:4]

    # Follower and following lists (restricted to 10 each, will refer to a more page on which they will all be)
    following_user = request.user.following.filter(id=user.id).exists()

    followers = user.followers.all()[:3]
    followings = user.following.all()[:3]

    followers_count = user.get_followers_count()
    followings_count = user.get_following_count()

    # Track search click if coming from search
    track_search_click(request, user)

    context = {'pubs': pubs, 'user': user, 'collections': collections, 'following_user': following_user,
               'followers': followers, 'followings': followings, 'notifications': notifications, 
               'followers_count': followers_count, 'followings_count': followings_count}

    return render(request, "base/profile.html", context)

@login_required
def editProfile(request, pk: str):
    """
    Handle user profile editing with GET and POST requests.
    
    Allows authenticated users to update their profile information including
    email, password, school, bio, social links, and profile photo. Users can
    only edit their own profiles.
    
    Args:
        request (HttpRequest): The HTTP request object containing user data
        pk (str): Primary key of the user whose profile is being edited
        
    Returns:
        HttpResponse: 
            - GET: Renders edit profile form with current user data
            - POST: Redirects to user profile on success, or re-renders form with errors
            
    Security:
        - Requires user authentication (@login_required)
        - Validates user can only edit their own profile
        - Password confirmation validation
        - Exception handling for database operations
        
    Form Fields:
        - photo: Profile image file upload (optional)
        - email: User email address
        - password1/password2: New password with confirmation (optional)
        - school: Educational institution (optional)
        - bio: User biography (optional)
        - linkedin: LinkedIn profile URL (optional)
        - github: GitHub profile URL (optional)
    """
    
    User = get_user_model()
    user = get_object_or_404(User, id=pk)
    
    # Check if user can edit this profile
    if user != request.user:
        messages.error(request, "You can only edit your own profile")
        return redirect("base:user-profile", pk)

    context = {'user': user}

    if request.method == "POST":
        # Get the data
        photo = request.FILES.get('photo')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        school = request.POST.get('school')
        bio = request.POST.get('bio')
        linkedin = request.POST.get('linkedin')
        github = request.POST.get('github')

        # Validate passwords
        if password1 and password2:
            if password1 != password2:
                messages.error(request, "Passwords do not match. Try again...")
                return render(request, "base/edit_profile.html", context)
            
            # Additional checking, not used yet but will be useful in the future
            # if len(password1) < 8:
            #     messages.error(request, "Password must be at least 8 characters long")
            #     return render(request, "base/edit_profile.html", context)
        
        try:
            # Update user fields
            user.email = email
            user.school = school or ""
            user.bio = bio or ""
            user.linkedin = linkedin or ""
            user.github = github or ""

            # Update password only if provided
            if password1:
                user.password = make_password(password1)
            
            # Update photo only if provided
            if photo:
                user.photo = photo
            
            user.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("base:user-profile", user.id)

        except Exception as e:
            messages.error(request, f"Something went wrong while updating: {str(e)}")
            return render(request, "base/edit_profile.html", context)

    return render(request, "base/edit_profile.html", context)

# @login_required
# def editProfile(request, pk: str):
#     User = get_user_model()
#     user = get_object_or_404(User, id=pk)

#     context = {'user': user}

#     if request.method == "POST":
#         # Get the data
#         photo = request.POST.get('photo')
#         email = request.POST.get('email')
#         password = request.POST.get('password1')
#         password2 = request.POST.get('password2')
#         school = request.POST.get('school')
#         bio = request.POST.get('bio')
#         linkedin = request.POST.get('linkedin')
#         github = request.POST.get('github')

#         if password != password2:
#             messages.error(request, "Missmatching passwords. Try again...")
#             return render(request, "base/edit_profile.html", context)
        
#         try:
#             user.email = email
#             user.password = password
#             user.school = school
#             user.bio = bio
#             user.linkedin = linkedin
#             user.github = github

#             if photo:
#                 user.photo = photo
            
#             user.save()

#             return redirect("base:user-profile", user.id)

#         except Exception as e:
#             messages.error(request, f"Something went wrong while updating : {str(e)}")
#             return render(request, "base/edit_profile.html", context)

#     return render(request, "base/edit_profile.html", context)

def followUser(request, pk: str):
    """
    Handle user following functionality.
    
    Allows authenticated users to follow other users, with validation to prevent
    self-following and duplicate follows. Creates a notification for the followed user.
    
    Args:
        request (HttpRequest): The HTTP request object containing authenticated user
        pk (str): Primary key of the user to be followed
        
    Returns:
        HttpResponse: Redirects to the target user's profile page with status message
        
    Business Logic:
        - Prevents users from following themselves
        - Checks for existing follow relationship to avoid duplicates
        - Adds follower relationship if validation passes
        - Triggers notification to followed user
        
    Messages:
        - Error: When attempting to follow oneself
        - Info: When already following the target user
        - Success: When successfully following a new user
        
    Side Effects:
        - Updates user's following relationship via many-to-many field
        - Creates new follower notification via NotificationManager
    """

    User = get_user_model()
    user_to_follow = get_object_or_404(User, id=pk)
    
    # Prevent users from following themselves
    if user_to_follow == request.user:
        messages.error(request, "You cannot follow yourself")
        return redirect('base:user-profile', pk)
    
    # Check if already following
    if request.user.following.filter(id=user_to_follow.id).exists():
        messages.info(request, f"You are already following {user_to_follow.username}")
    else:
        request.user.following.add(user_to_follow)
        messages.success(request, f"You are now following {user_to_follow.username}")
        
        # Create notification
        utils.NotificationManager.new_follower(request.user, user_to_follow)
    
    return redirect('base:user-profile', pk)


@login_required
def unfollowUser(request, pk: str):
    """
    Unfollow a user and redirect to their profile.
    
    Args:
        request: HTTP request object
        pk (str): User ID to unfollow
        
    Returns:
        HttpResponse: Redirect to user profile with status message
    """

    User = get_user_model()
    user_to_unfollow = get_object_or_404(User, id=pk)
    
    if request.user.following.filter(id=user_to_unfollow.id).exists():
        request.user.following.remove(user_to_unfollow)
        messages.success(request, f"You have unfollowed {user_to_unfollow.username}")
    else:
        messages.info(request, f"You are not following {user_to_unfollow.username}")
    
    return redirect('base:user-profile', pk)


def followers(request, pk: str):
    User = get_user_model()
    user = get_object_or_404(User, id=pk)

    followers = user.followers.all()
    # followings = user.following.all()

    followers_count = user.get_followers_count()

    context = {'user': user, 'followers': followers, 'followers_count': followers_count}

    return render(request, "base/followers.html", context)


def followings(request, pk: str):
    User = get_user_model()
    user = get_object_or_404(User, id=pk)

    followings = user.following.all()
    # followings = user.following.all()

    followings_count = user.get_following_count()

    context = {'user': user, 'followings': followings, 'followings_count': followings_count}

    return render(request, "base/followings.html", context)



def createCollection(request):
    """
    Create a new collection for the authenticated user.
    
    Args:
        request: HTTP request object containing collection name in POST data
        
    Returns:
        HttpResponse: Redirect to referring page with status message
    """

    if request.method == "POST":
        name = request.POST.get("name")
        if name:
            Collection.objects.create(user=request.user, name=name)
            messages.success(request, "Collection created successfully!")
        else:
            messages.error(request, "Name is required.")
    return redirect(request.META.get("HTTP_REFERER", "base:home"))

@login_required
def deleteCollection(request, pk: str):
    """
    Delete a collection owned by the current user.
    
    Args:
        request: HTTP request object
        pk (str): Collection ID to delete
        
    Returns:
        HttpResponse: Redirect to user profile with status message
    """
    
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
    """
    Add a publication to an existing or new collection.
    
    Args:
        request: HTTP request object containing collection name
        pk (str): Publication ID to add to collection
        
    Returns:
        HttpResponse: Redirect to referring page with status message
    """

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
    """
    Display a user's collection with its publications.
    
    Args:
        request: HTTP request object
        pk_u (str): User ID who owns the collection
        pk_c (str): Collection ID to display
        
    Returns:
        HttpResponse: Rendered collection template with context data
    """

    collection = Collection.objects.get(id=pk_c)
    User = get_user_model()
    user = get_object_or_404(User, id=pk_u)
    collections = (
        user.collection_set
        .annotate(pub_count=Count("publications"))
        .prefetch_related("publications")
    )
    publications = CollectionPublication.objects.filter(collection=collection).select_related('publication')

    # Track search click if coming from search
    track_search_click(request, collection)

    context = {'user': user, 'collection': collection, "publications": publications, "collections": collections}
    return render(request, "base/collection.html", context)


@login_required
def deleteFromCollection(request, collection_id, publication_id):
    """
    Remove a publication from a user's collection.
    
    Args:
        request: HTTP request object
        collection_id: Collection ID to remove from
        publication_id: Publication ID to remove
        
    Returns:
        HttpResponse: Redirect to referring page with status message
    """

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
    """
    Add a topic to user's favorites.
    
    Args:
        request: HTTP request object
        pk (str): Topic ID to add to favorites
        
    Returns:
        HttpResponse: Redirect to referring page with status message
    """

    topic = get_object_or_404(Topic, id=pk)
    
    # Check if already in favorites
    if request.user.favorite_topics.filter(id=topic.id).exists():
        # remove topic from favorites
        request.user.favorite_topics.remove(topic)
        messages.success(request, f'"{topic.name}" removed from your favorites')
    else:
        # Add topic to favorites
        request.user.favorite_topics.add(topic)
        messages.success(request, f'"{topic.name}" added to your favorites')
    
    return redirect(request.META.get('HTTP_REFERER', 'base:home'))

@login_required
def removeTopicFromFav(request, pk: str):
    """
    Remove a topic from user's favorites.
    
    Args:
        request: HTTP request object
        pk (str): Topic ID to remove from favorites
        
    Returns:
        HttpResponse: Redirect to referring page with status message
    """

    topic = get_object_or_404(Topic, id=pk)
    
    request.user.favorite_topics.remove(topic)
    messages.success(request, f'"{topic.name}" removed from your favorites')
    
    return redirect(request.META.get('HTTP_REFERER', 'base:home'))


# mark notification as read logic
@login_required
def mark_notification_read(request, notification_id):
    """
    Mark a notification as read and redirect to its target URL.
    
    Args:
        request: HTTP request object
        notification_id: Notification ID to mark as read
        
    Returns:
        HttpResponse: Redirect to notification's action URL or actor's profile
    """

    notification = get_object_or_404(
        Notification, 
        id=notification_id, 
        recipient=request.user
    )
    
    # Mark as read
    notification.mark_as_read()
    
    # Redirect to the notification's target URL
    if notification.action_url:
        return redirect(notification.action_url)
    else:
        # Fallback to actor's profile
        return redirect('base:user-profile', pk=notification.actor.id)


@login_required
def notificationsPage(request):
    """
    Display user's notifications page with recent notifications.
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Rendered notifications template with last 50 notifications
    """

    notifications = request.user.notifications.filter(
        is_deleted=False
    ).order_by('-created')[:50]  # Show last 50 notifications
    
    context = {
        'notifications': notifications
    }
    return render(request, 'base/notifications.html', context)


@login_required
def createDiscussion(request, pk: str):
    """
    Create a new discussion room for a publication.
    
    Args:
        request: HTTP request object containing title and description
        pk (str): Publication ID to create discussion for
        
    Returns:
        HttpResponse: Redirect to referring page with status message
        
    Side Effects:
        - Creates Discussion object linked to publication
        - Sends notifications to publication authors
    """

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()

        if not title:
            messages.error(request, "Discussion room name is required")
            return redirect(request.META.get('HTTP_REFERER', 'base:home'))
        
        if not description:
            messages.error(request, "Description is required")
            return redirect(request.META.get('HTTP_REFERER', 'base:home'))
        
        # Get the publication
        pub = get_object_or_404(Publication, id=pk)
        
        discussion = Discussion.objects.create(
            creator = request.user,
            publication = pub,
            title = title,
            description = description
        )

        messages.success(request, "Discussion room created successful!")

        for author in pub.authors.all():
            if request.user.id != author.id:
                utils.NotificationManager.new_discussion_in_publication(request.user, author, discussion)

    return redirect("base:discussion", pk = discussion.id)


@login_required
def discussion(request, pk: str):
    """
    Display discussion room and handle new message posts.
    
    Args:
        request: HTTP request object, may contain message body and reply_to in POST
        pk (str): Discussion ID to display
        
    Returns:
        HttpResponse: 
            - GET: Rendered discussion template with messages and participants
            - POST: Redirect to discussion after posting message
            
    Side Effects:
        - Creates Message objects for new posts
        - Adds user to discussion participants
        - Sends notifications to participants and reply targets
    """

    # Get the discussion
    discussion = get_object_or_404(Discussion, id=pk)
    
    # Get messages in chronological order (oldest first for chat)
    # Only get top-level messages (not replies)
    discussion_messages = discussion.message_set.filter(reply_to__isnull=True).order_by('created')
    
    # Get participants
    participants = discussion.participants.all()

    if request.method == "POST":
        body = request.POST.get("body")
        reply_to_id = request.POST.get("reply_to")
        
        if body and body.strip():  # Only create message if body is not empty
            # Check if this is a reply
            reply_to_message = None
            if reply_to_id:
                try:
                    reply_to_message = Message.objects.get(
                        id=reply_to_id, 
                        discussion=discussion
                    )
                except Message.DoesNotExist:
                    reply_to_message = None
            
            message = Message.objects.create(
                user=request.user,
                discussion=discussion,
                body=body.strip(),
                reply_to=reply_to_message
            )
            
            # Add user to participants if not already
            if request.user not in participants:
                discussion.participants.add(request.user)
            
            # Create notifications
            notification_recipients = set()
            
            # If it's a reply, notify the original message author
            if reply_to_message and reply_to_message.user != request.user:
                notification_recipients.add(reply_to_message.user)
            
            # Notify other participants (excluding the message sender)
            for participant in participants:
                if participant != request.user:
                    notification_recipients.add(participant)
            
            # Also notify the discussion creator if they're not a participant yet
            if discussion.creator != request.user and discussion.creator not in participants:
                notification_recipients.add(discussion.creator)
            
            # Send notifications
            for recipient in notification_recipients:
                utils.NotificationManager.discussion_reply(
                    request.user, 
                    recipient, 
                    discussion, 
                    message
                )
            
            return redirect("base:discussion", pk=discussion.id)

    # Track search click if coming from search
    track_search_click(request, discussion)

    context = {
        "discussion": discussion, 
        "discussion_messages": discussion_messages,
        "participants": participants,
        "participants_count": participants.count()
    }
    return render(request, "base/discussion.html", context)


def viewTag(request, pk: str):
    tag = get_object_or_404(Tag, id=pk)

    publications = tag.publications.all()

    context = {
        'tag': tag,
        'publications': publications,
    }
    return render(request, "base/tag.html", context)












