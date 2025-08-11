from utils.decorateurs import log_action
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model


def signUp_view(request):
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
            return render(request, 'inscription.html')

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
            return render(request, 'inscription.html')

    return render(request, 'inscription.html')

@log_action('login')
def login_view(request):
    """
    View for user login.
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
                return redirect('home')  # Redirect to home page after login
            else:
                messages.error(request, 'Mot de passe incorrect.')
        except get_user_model().DoesNotExist:
            messages.error(request, 'Utilisateur non trouvé.')


    return render(request, 'login.html')

@log_action('logout')
def logout_view(request):
    """
    View for user logout.
    """
    from django.contrib.auth import logout
    logout(request)
    request.session.flush()  # Clear the session
    return redirect('authentification:login') 

def profile_view(request):
    """
    View for user profile.
    """
    return render(request, 'login.html') 
