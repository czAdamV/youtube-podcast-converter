.. ytfeed documentation master file, created by
   sphinx-quickstart on Fri Feb  7 15:03:40 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Ytfeed
======


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules


Intruduction
############

Ytfeed is a minimalistic service generating RSS and ATOM podcasts from YouTube
playlists. Try it out in Docker!

.. code-block:: Text

   $ docker build . -t ytfeed
   $ docker run -p 80:80 ytfeed
   $ vlc http://localhost/PLFsQleAWXsj_4yDeebiIADdH5FMayBiJo.rss
   $ # atom feed on http://localhost/PLFsQleAWXsj_4yDeebiIADdH5FMayBiJo.atom


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
