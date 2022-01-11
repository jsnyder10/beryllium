#Starting
cd to beryllium directory
source env/bin/activate
FLASK_DEBUG=1 flask run
#goto browser
127.0.0.1:5000

#Installing
git clone url
cd to beryllium folder
virtualenv env
pip install -r requirements.txt
flask db upgrade
FLASK_DEBUG=1 flask run
#goto browser
127.0.0.1:5000