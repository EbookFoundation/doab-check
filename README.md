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