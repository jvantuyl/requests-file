from cgi import escape as html_escape
from email.utils import formatdate
import errno
from mimetypes import guess_type as guess_mime_type
from os import listdir, readlink, stat, strerror, unlink
from os.path import abspath, exists
from stat import S_ISDIR, S_ISLNK, S_ISREG
from StringIO import StringIO
from traceback import format_exc
from urllib import quote as url_quote, unquote as url_unquote
from requests import Response
from requests.adapters import BaseAdapter
from requests.exceptions import RequestException, InvalidURL
from requests.hooks import dispatch_hook


class UnsupportedFeature(RequestException):
    """Adapter doesn't support this feature."""


class FileAdapter(BaseAdapter):
    """adapter implemented against the filesystem"""
    # TODO: conditional requests?
    # TODO: idempotent put?
    # TODO: range requests?
    # TODO: logging?
    # TODO: other verbs, OPTIONS, etc.
    # TODO: content-type/encoding negotiation
    # TODO: confine to some directory?
    # TODO: weirder encoding rules (i.e. UTF-8, %-encoding for UTF-8 filenames)

    def send(
            self, request, stream=False, verify=None, cert=None, proxies=None,
            timeout=None
        ):
        """issue request"""

        fname = url_unquote(request.url[len('file://'):])
        if not fname:
            raise InvalidURL('missing file name')
        if '/' not in fname:
            raise InvalidURL(
                'hostname without filename (perhaps missing a /?)'
            )
        host, fname = fname.split('/', 1)
        fname = self.resolve_host(host, fname)

        response = Response()
        response.url = request.url
        response.headers['Date'] = formatdate(timeval=None, localtime=True)

        try:
            if request.method in ('GET', 'HEAD'):
                statdata = stat(fname)
                etag = '"%s/%s/%s' \
                    % (statdata.st_dev, statdata.st_ino, statdata.st_mtime)
                if S_ISLNK(statdata.st_mode):
                    # handle relative symlinks!
                    target_file = abspath(readlink(fname))
                    response.status_code = 302
                    response.headers['Status'] = '302 Found'
                    response.headers['Location'] = \
                        url_quote('file://' + target_file)
                elif S_ISDIR(statdata.st_mode):
                    response.status_code = 200
                    response.headers['Status'] = '200 Ok'
                    body = \
                        """<html><head><title>%s</title></head><body><ul>""" \
                        % fname
                    for subfname in sorted(listdir(fname)):
                        body += '<li><a href="file://' + \
                                url_quote(subfname) + '">' + \
                                html_escape(fname) + '</a></li>'
                    body += '</body></html>'
                    response.headers['ETag'] = 'W/' + etag
                    response.raw = StringIO(body)
                elif S_ISREG(statdata.st_mode):
                    response.status_code = 200
                    response.headers['Content-Length'] = statdata.st_size
                    response.headers['Last-Modified'] = formatdate(
                        timeval=statdata.st_mtime,
                        localtime=True
                    )
                    mt, enc = guess_mime_type(request.url, strict=False)
                    if mt is None:
                        mt = 'application/octet-stream'
                    if enc is not None:
                        response.headers['Content-Encoding'] = enc
                    response.headers['Content-Type'] = mt
                    response.headers['ETag'] = etag
                    if request.method == 'GET':
                        response.raw = open(fname, 'r')
                else:
                    response.status_code = 500
                    response.headers['Status'] = '500 Internal Server Error'
            elif request.method == 'PUT':
                open(fname, 'w').write(request.body)  # FIXME: Is this right?
                response.status_code = 200
                response.headers['Status'] = '200 Ok'
            elif request.method == 'POST':
                if exists(fname):  # FIXME: Is this right?
                    response.status_code = 409
                    response.headers['Status'] = '409 Conflict'
                else:
                    open(fname, 'w').write(request.body)
            elif request.method == 'DELETE':
                unlink(fname)
                response.status_code = 200
                response.headers['Status'] = '200 Ok'
            else:
                response.status_code = 405
                response.headers['Status'] = '405 Method Not Allowed'
        except OSError as e:
            if e.errno == errno.ENOENT:
                if request.method == 'DELETE':
                    response.status_code = 410
                    response.headers['Status'] = '410 Gone'
                else:
                    response.status_code = 404
                    response.headers['Status'] = '404 Not Found'
            elif e.errno == errno.EISDIR:
                response.status_code = 405
                response.headers['Status'] = '405 Method Not Allowed'
                response.raw = StringIO('Cannot %r a directory...'
                    % request.method)
            elif e.errno == errno.EACCES:
                response.status_code = 403
                response.headers['Status'] = '403 Forbidden'
            else:
                response.status_code = 500
                response.headers['Status'] = '500 Internal Server Error'
                response.raw = StringIO('OSError: ' + strerror(e.errno))
        except Exception:
            response.status_code = 500
            response.headers['Status'] = '500 Internal Server Error'
            response.raw = StringIO(format_exc())

        # context
        response.request = request
        response.connection = self

        # hooks
        response = dispatch_hook('response', request.hooks, response)

        # streaming
        if not stream:
            response.content

        return response

    def resolve_host(self, host, fname):
        if host and host != 'localhost':
            raise UnsupportedFeature(
                "file scheme doesn't support non-local files at this time"
            )
        else:
            return '/' + fname

    def close(self):
        """close connection (currently doesn't do anything)"""
