"""
WSGI config for ytexplains project.
"""

import os
from django.core.wsgi import get_wsgi_application
from django.core.management import execute_from_command_line


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ytexplains.settings')

application = get_wsgi_application()
app = application  # Add this line for Vercel

if __name__ == "__main__":
    execute_from_command_line(sys.argv)