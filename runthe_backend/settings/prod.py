from glob import glob
from runthe_backend.settings._base import *
from dotenv import load_dotenv

load_dotenv()
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
IS_DEBUG=False