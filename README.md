# fullyaliveretreat

A django website for registering, receiving payment through PayPal, and sending email notifications for camp.

# Things to Install
1. Install from link [python 3]
1. Add to Environment Variables the Path ;C:
1. Downlaod pip 
    1. Command line way: curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    1. A different way [tutorial](https://www.liquidweb.com/kb/install-pip-windows/)
1. Install pip
    1. cmd line: python get-pip.py
1. Add to Environment Variables the path ;C: (same way as above)

# To get the website running on a windows machine
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
