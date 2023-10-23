# doab-check
 Link and DB Checker for DOAB
 
 
 ## update
 
 ```
 cd doab-check
 git fetch origin
 git checkout remotes/origin/main
 pipenv shell

 python manage.py migrate
 sudo systemctl restart gunicorn
 
```

## resize droplet

```
 poweroff
```
reconfigure in console
power on button

```
 sudo restart nginx
 sudo restart gunicorn
```

## initial config 
https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-18-04