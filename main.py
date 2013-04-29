import datetime
import urllib
import webapp2
import jinja2
import os

from google.appengine.ext import db
from google.appengine.api import users


JINJA_ENVIRONMENT = jinja2.Environment(loader=jinja2.FileSystemLoader(
    os.path.dirname(__file__)))

JINJA_ENVIRONMENT.globals.update(zip=zip)


class BaseRequestHandler(webapp2.RequestHandler):

    def seeother(self, uri):
        self.response.set_status(303)
        import urlparse
        absolute_url = urlparse.urljoin(self.request.uri, uri)
        self.response.headers['Location'] = str(absolute_url)
        self.response.clear()

    def notfound(self):
        self.response.set_status(404)
        self.response.clear()

    def set_cookie(self, key, value='', max_age=None, path='/', domain=None, secure=None):
        """
        Set (add) a cookie for the response
        """
        header = key + '=' + urllib.quote(value)
        if max_age:
            import datetime
            header += '; expires=' + (datetime.datetime.now() +
                                      datetime.timedelta(seconds=max_age)).strftime("%a, %d %b %Y %H:%M:%S GMT")
        if path != '/':
            header += '; path=' + path
        if domain is not None:
            header = '; domain=' + domain
        if secure is not None:
            header = '; secure=' + str(secure)
        self.response.headers.add_header('Set-Cookie', header)

    def clear_cookie(self, key):
        self.response.headers.add_header('Set-Cookie', key + '=; expires=Tue, 01 Jan 2008 00:00:00 GMT')


class Upvote(BaseRequestHandler):

    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Hello, webapp2 World!')


class Downvote(BaseRequestHandler):

    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Hello, webapp2 World!')


class Poll(db.Model):
    """Models an individual Guestbook entry with author, content, and date."""
    title = db.StringProperty()
    n_problems = db.IntegerProperty()
    problem_titles = db.StringListProperty()
    votes = db.ListProperty(int)
    created = db.DateTimeProperty(auto_now_add=True)


class AddPoll(BaseRequestHandler):
    def get(self):
        user = users.get_current_user()
        if users.is_current_user_admin():
            self.response.write(JINJA_ENVIRONMENT.get_template('add.html').render({}))
        else:
            self.seeother('/')

    def post(self):
        if users.is_current_user_admin():
            title = self.request.get('title')
            problem_titles = filter(lambda t: t.strip() != '', self.request.get('problem_titles').split('\n'))
            Poll(title=title,
                 n_problems=len(problem_titles),
                 problem_titles=problem_titles,
                 votes=[0] * len(problem_titles)).put()
        self.seeother('/')


class DeletePoll(BaseRequestHandler):
    def get(self):
        if users.is_current_user_admin():
            pkey = self.request.get('pkey')
            poll = Poll.get(pkey)
            if poll:
                poll.delete()
        self.seeother('/')


class ViewPoll(BaseRequestHandler):
    def get(self):
        pkey = self.request.get('pkey')
        poll = Poll.get(pkey)
        if not poll:
            self.notfound()
        else:
            template = JINJA_ENVIRONMENT.get_template('view.html')
            self.response.write(template.render({'poll': poll}))


class MainPage(BaseRequestHandler):

    def get(self):
        template = JINJA_ENVIRONMENT.get_template('index.html')
        user_logged = users.get_current_user()

        params = {'login_link': users.create_login_url(self.request.uri)
                                if not user_logged else users.create_logout_url('/'),
                  'login_text': 'admin' if not user_logged else 'logout',
                  'all_polls': Poll.all().order('-created').fetch(100),
                  'admin': users.is_current_user_admin()}

        self.response.write(template.render(params))

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/add', AddPoll),
                               ('/del', DeletePoll),
                               ('/view', ViewPoll)
                              ],
                              debug=True)
