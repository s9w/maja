# dampy
dampy collects posts from sites you regularly visit (Reddit, Hacker News, Stack Exchange) depending on defined criteria and presents them in a central place. 

## Motivation
Many developers visit Hacker News, Stack Exchange or Reddit daily to keep up to date. This can't be easily automated like RSS feeds from a blog, since only a small fraction of the many posts is relevant.

With dampy you can define minimum scores and specific keywords for each of the sites. Matching posts get fetched in regular intervals, stored in a database and presented on a simple web interface. This approach is much more time-efficient and will catch things even if you are away for longer periods of time.

## Usage
Dampy is Python program than reads its configuration from the 'jobs.json' file. It contains a list of *jobs* of types `HN` (Hacker news), `SE` (Stack Exchange) or `reddit` (Reddit).

Every job has a `score` property, which defines the minimum score (upvotes or score, depending on the site) the post must have to be considered. For Reddit, you must also specify a `subreddit`. For Stack Exchange, you must specify a `site` like `stackoverflow` or `tex`. Stack Exchange entries entries can also have a `tags` property to further limit the results to questions with those tags. That way you can only look at `python` questions at stackoverflow for example.

Hacker News and Reddit also support a `keyword` property, which is a search term. You can have multiple jobs for the same site. As an example, if you want all Hacker News posts with a score >=200, but also want to see those mentioning "physics" that are >=20, an example `jobs.json` would look like:

	[
	  {
	    "type": "HN",
	    "score": 200
	  },
	  {
	    "type": "HN",
	    "keyword": "physics",
	    "score": 20
	  }
	]

The web interface lists the posts from new to old. They are grouped by "subtype" (subreddit/site for Reddit/Stack Exchange; HN has no subtypes). Clicking the green arrow on the left will mark that post and every one below it (everything older) in the same group as read. Those will not show up next time.

## Stack Exchange API setup
Stack Exchange requires the app to be authorized by the user to increase its API limits. Dampy does **not** not use this authentification to access *any* user data. But there is no way to authenticate without this access.

To authenticate, go to [https://stackexchange.com/oauth/dialog?client_id=8691&scope=no_expiry&redirect_uri=https://stackexchange.com/oauth/login_success](this) site and accept. You'll be redirected to another site. From its url, copy the string after `access_token=` into the `se_access_token` value in `secrets.json".`

## Philosophy and design
The entire program was designed with simplicity in mind, allowing for easy extension and customization. The interfaces for the three supported sites are defined in files only ~100 lines each, and the main program is about ~200. This should make support for other sites simple.

The posts are stored in a straightforward SQLite database which is used to populate a Flask web interface. The interface is an easily modified Jinja2 template and css file.