requests-file: File Scheme for Requests
=======================================

'file' URL scheme support for the popular Requests HTTP Library.

Example:

    from requests import Session
    from requests_file.adapters import FileAdapter

    s = Session()
    s.mount('file://', FileAdapter())
    r = s.get('file:///path/to/some/file.txt')
    print(r.code)
    print(r.content)


Caveats
-------

Some versions of requests require a host to be specified in the file URL.
These don't like the common case for file URLs where the host is omitted
(meaning localhost).  You'll have to update to a version of requests containing
the following patch:

https://github.com/jvantuyl/requests/commit/90b37b30351cb8064aeafdfc442685590cdc9821


Authors
--------
Copyright (C) 2013, Jayson Vantuyl <jayson@aggressive.ly>
