## Folder/ Authentification

### Functionalities

This folder contains all files related to the authentification process. As a basic, it holds two functionalities:

- User registration: if user doesn't have an account, he can create one through the route `authentification:signUp -> /register/`. The user is then returned to the log in page (through route `authentification:login -> /login/`) where he has to log in and then start navigation in home page (`base:home -> /`).

- User log in: if user does already have an account, he can log into his account and start the navigation right away.


### Technical details

We implement these functionalities here by creating a custom user model (extending Django's `AbstractUser` class). This new user class holds additional properties for our goal. We have implemented these


```bash
photo = models.ImageField(upload_to='profils/', default='profils/avatar.svg')
school = models.CharField(max_length=100, default='ENSAE Dakar')
bio = models.TextField(blank=True, null=True)
linkedin = models.URLField(blank=True, null=True)
github = models.URLField(blank=True, null=True)
slug = models.SlugField(unique=True, blank=True, null=True)
nb_documents = models.PositiveIntegerField(default=0)
```

These are requested for input in the register phase. But in the login page only the user's username and password are requested for authentification.

The framework is the following:

User (no account) asks for login -> redirected to the login page (`authentification/templates/login.html`). 

If account available, inputs username and password -> login success -> redirect to home page (`base/templates/home.html`) with all his content.

If account not available, has to go to the register page `authentification/templates/inscription.html` -> inputs all fields required for user account and validates -> redirect to the login page (`templates/login.html`) -> now account available -> logs in and sent back to home page







