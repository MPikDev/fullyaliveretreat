# fullyaliveretreat

A django website for registering, receiving payment through PayPal, and sending email notifications for camp.

## Things to Install
1. Install from link [python 3]
1. Add to Environment Variables the Path ;C:
1. Downlaod pip 
    1. Command line way: curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    1. A different way [tutorial](https://www.liquidweb.com/kb/install-pip-windows/)
1. Install pip
    1. cmd line: python get-pip.py
1. Add to Environment Variables the path ;C: (same way as above)

## To get the website running on a windows machine
1. pip install virtualenv
1. get a clone of the repo if not already then go into the camp_registration_website directory
1. virtualenv venv 
1. venv\Scripts\activate 
1. pip install -r requirements.txt
1. in personal_code directory the local_settings_copy remove the _copy from the file name
1. python manage.py runserver
1. Stop server: ctrl c for linux/mac
1. python manage.py makemigrations 
1. python manage.py migrate 
1. python manage.py createsuperuser ` remember the username and password `
1. python manage.py runserver


# Update seciton 04/02/2025

## Dillon Homebrew Install
1. https://docs.brew.sh/Installation

## Dillon Pip Install
1. https://phoenixnap.com/kb/install-pip-mac
2. `python3 -m ensurepip`

## Dillon Getting Running on M3 Mac
1. `pip install virtualenv`
2. If you haven't cloned then `git clone https://github.com/MPikDev/camp_registration_website.git` Else go to project root directory
3. `brew install pyenv-virtualenv`
4. `exec $SHELL` 
5. `pyenv virtualenvs`
6. `pyenv virtualenv 3.8 myenv`
7. `source ~/.pyenv/versions/myenv/bin/activate`
8. `pip install -r requirements.txt`
9. `python manage.py runserver`
10. To Stop the Server: ctrl+c for linux/mac

## Dillon Making Migrations
1. `python manage.py makemigrations`
2. `python manage.py migrate`

## Dillon Making an Admin User
1. `python manage.py createsuperuser` REMEMBER the username and password!

