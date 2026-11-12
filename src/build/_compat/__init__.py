__lazy_modules__ = {f'{__spec__.parent}.tarfile'}

from .tarfile import tarfile as archive_tarfile


__all__ = ['archive_tarfile']
