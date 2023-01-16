import sys, runpy
activate_this = '/home/microservices/payments/venv/bin/activate_this.py'
runpy.run_path(activate_this)
sys.path.insert(0,'/home/microservices/payments')

from wsgi import app as application
