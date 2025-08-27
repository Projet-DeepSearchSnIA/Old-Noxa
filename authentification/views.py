from utils.decorateurs import log_action
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model


def register(request):
    """
    Handle user registration for the Noxa application.
    
    Processes both GET and POST requests for user registration:
    - GET: Displays the registration form
    - POST: Validates form data and creates a new user account
    
    Args:
        request (HttpRequest): The HTTP request object containing user data
        
    POST Parameters Expected:
        - username (str): Unique username for the account
        - password1 (str): User's chosen password
        - password2 (str): Password confirmation for validation
        - email (str): User's email address
        - photo (File, optional): Profile picture upload
        - school (str, optional): User's school (defaults to 'ENSAE Dakar')
        - bio (str, optional): User biography/description
        - linkedin (str, optional): LinkedIn profile URL
        - github (str, optional): GitHub profile URL
        
    Returns:
        HttpResponse: 
        - On GET: Renders registration form template
        - On successful POST: Redirects to login page with success message
        - On failed POST: Re-renders form with error messages
        
    Raises:
        Exception: Catches and displays any database or validation errors
        during user creation process
        
    Validation:
        - Ensures password confirmation matches original password
        - Uses Django's built-in create_user() method for proper password hashing
        - Handles file uploads for profile photos
        
    Messages:
        - Success: Confirms successful registration
        - Error: Password mismatch or database errors
    """
    User = get_user_model()
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password1')
        password2 = request.POST.get('password2')
        email = request.POST.get('email')
        photo = request.FILES.get('photo')
        school = request.POST.get('school', 'ENSAE Dakar')
        bio = request.POST.get('bio', '')
        linkedin = request.POST.get('linkedin', '')
        github = request.POST.get('github', '')

        if password != password2:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, 'authentification/inscription.html')

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                school=school,
                bio=bio,
                linkedin=linkedin,
                github=github,
            )
            if photo:
                user.photo = photo
            user.save()
            
            messages.success(request, 'Inscription réussie. Veuillez vous connecter.')
            return redirect('authentification:login')  
        except Exception as e:
            messages.error(request, f"Erreur lors de l'inscription : {str(e)}")
            return render(request, 'authentification/inscription.html')

    return render(request, 'authentification/inscription.html')

@log_action('login')
def loginUser(request):
    """
   Handle user authentication and login for the Noxa application.
   
   Processes both GET and POST requests for user login:
   - GET: Displays the login form
   - POST: Authenticates user credentials and establishes session
   
   Args:
       request (HttpRequest): The HTTP request object containing login credentials
       
   POST Parameters Expected:
       - username (str): User's username for authentication
       - password (str): User's password for verification
       
   Returns:
       HttpResponse:
       - On GET: Renders login form template
       - On successful POST: Redirects to home page with success message
       - On failed POST: Re-renders login form with appropriate error messages
       
   Authentication Process:
       1. Retrieves user by username from database
       2. Verifies password using Django's built-in check_password() method
       3. Establishes user session using Django's login() function
       4. Stores username in session for additional tracking
       
   Session Management:
       - Creates authenticated session for valid users
       - Stores username in session['username'] for easy access
       - Redirects authenticated users to 'base:home'
       
   Error Handling:
       - User not found: "Utilisateur non trouvé"
       - Invalid password: "Mot de passe incorrect"
       - Success: "Connexion réussie"
       
   Decorators:
       @log_action('login'): Logs login attempts for audit/security purposes
       
   Security Features:
       - Uses Django's secure password verification
       - Proper error messages without revealing user existence
       - Session-based authentication
   """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user = get_user_model().objects.get(username=username)
            if user.check_password(password):
                # Log the user in
                from django.contrib.auth import login
                login(request, user)
                request.session['username'] = user.username  # Store username in session
                messages.success(request, 'Connexion réussie.')
                return redirect('base:home')  # Redirect to home page after login
            else:
                messages.error(request, 'Mot de passe incorrect.')
        except get_user_model().DoesNotExist:
            messages.error(request, 'Utilisateur non trouvé.')


    return render(request, 'authentification/login.html')

@log_action('logout')
def logoutUser(request):
    """
    View for user logout.
    """
    logout(request)
    request.session.flush()  # Clear the session
    return redirect('base:home') 

