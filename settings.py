# settings.py

try:
    from local_settings import *
except ModuleNotFoundError:
    from prod_settings import *
except ImportError:
    from prod_settings import *
