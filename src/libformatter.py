import praw
import re
from src import config

LIBVER = "Alpha1.0"


class PostFormatter():
    """Parent class for all formatters.
    Formatters take Reddit posts as
    input and outputs a savable medium
    (eg. text or html)"""

    def __init__(self, post):
        self.post = post
        self.filetype = None

    def get_title(self):
        raise NotImplementedError()

    def get_author(self):
        raise NotImplementedError()

    def get_selftext(self):
        raise NotImplementedError()

    def get_comments(self):
        raise NotImplementedError()

    def parse_comment(self, comments, lvl=0):
        li = []
        for cmt in comments:
            li.append((cmt, lvl))
            # We add an indent to the comment string relative to its reply depth,
            # add the same indent to any newlines in the string and append it
            # to our return var
            if cmt.replies is not None:
                li.extend(self.parse_comment(cmt.replies, lvl+1))

        return li

    def format_comment(self, comment, lvl):
        raise NotImplementedError()

    def out(self):
        raise NotImplementedError()


class TextFormatter(PostFormatter):
    """Formats posts as plaintext."""

    def __init__(self, *args, **kwargs):
        super(TextFormatter, self).__init__(*args, **kwargs)
        self.filetype = ".txt"


    def get_author(self):
        return self.post.author.name if self.post.author is not None else "[deleted]"

    def get_title(self):
        return self.post.title if self.post.title is not None else "[deleted]"

    def get_selftext(self):
        if self.post.selftext is not None:
            lines = "-" * len(max(self.post.selftext.split("\n"), key=len))
            return "%s\n%s\n%s" % (lines, self.post.selftext, lines)
        else:
            return "---------\n[deleted]\n---------"

    def get_comments(self):

        comments = self.parse_comment(self.post.comments)
        return "".join([self.format_comment(cmt[0], cmt[1]) for cmt in comments])

    def format_comment(self, comment, lvl):
        # NASA has extensively researched and concluded there is no cleaner way to do this.
        stri = (
                "\n\n%s" % ("\t" * lvl) +
                (comment.author.name if comment.author is not None else "[deleted]") +
                " | " +
                str(comment.score if comment.score is not None else "[deleted]") +
                " points" +
                " | posted on " +
                str(comment.created_utc if comment.created_utc is not None else "[deleted]") +
                ("\n[" + comment.body + "]").replace("\n", "\n%s" % ("\t" * lvl))
        )
        return stri

    def out(self):
        self.post.comments.replace_more(limit=None)
        return (
                "(Note: Windows notepad does not display indentation correctly. "
                + "Copying this into a third-party text editor (eg. notepad++) may be favorable.)\n"
                + self.get_title()
                + "\nby "
                + self.get_author()
                + " on "
                + str(self.post.created_utc)
                + "\n"
                + self.get_selftext()
                + "\n"
                + "\n\nComments:"
                + self.get_comments()
                + "\n\n\n\n\n(Generated by: ArchiveIt bot ver. %s by /u/jman005)" % LIBVER
        )


class HTMLFormatter(PostFormatter):
    def __init__(self, *args, **kwargs):
        super(HTMLFormatter, self).__init__(*args, **kwargs)
        self.filetype = ".html"

    def get_author(self):
        '''cool!'''
        return "<p>$post.author.name</p><br>" if self.post.author is not None else "[deleted]"

    def get_selftext(self):
        return "<p>$post.selftext\n</p><br>" if self.post.is_self else "\n\n"

    def get_comments(self):
        return """#for $comment in $parsed_comments
        <p>#echo $format_comment($comment[0], 0)#</p>
        <br>
        #end for"""

    def format_comment(self, comment, lvl):
        return comment.body

    def out(self):
        topframe = """
        <html>
        <style>
        """
        self.post.comments.replace_more(limit=None)
        template = self.get_author() + self.get_selftext() + self.get_comments()
        return Template(template,
                        searchList=[
                            {'format_comment': self.format_comment,
                             'post': self.post,
                             'parsed_comments': self.parse_comment(self.post.comments)}
                        ]
                        )


def get_format(stri):
    if re.match(".?[Tt]ext.?", stri) is not None:
        return TextFormatter

    elif re.match(".?[Hh]tml.?", stri) is not None:
        return HTMLFormatter

    return None


reddit = praw.Reddit(user_agent=config.get_useragent(),
                     username=config.get_username(),
                     password=config.get_password(),
                     client_id=config.get_clientid(),
                     client_secret=config.get_clientsecret()
                     )

subm = reddit.submission('9nut40')
with open('testfile.html', 'w') as f:
    f.write(str(HTMLFormatter(subm).out()))


