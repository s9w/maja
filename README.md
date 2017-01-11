# dampy
dampy collects posts from sites you regularly visit (Reddit, Hacker News, Stack Exchange) depending on defined criteria and presents them in a central place. 

## Motivation
Many developers visit Hacker News, Stack Exchange or Reddit daily to keep up to date. This can't be easily automated like RSS feeds from a blog, since only a small fraction of the many posts is relevant.

With dampy you can define minimum scores and specific keywords for each of the sites. Matching posts get fetched in regular intervals, stored in a database and presented on a simple web interface. This approach is much more time-efficient and will catch things even if you are away for longer periods of time.

## Usage
The **jobs** are read from a `jobs.json` file. The SQLite database file is created in (or read from) the same folder. The config file contains a list of jobs of types `HN` (Hacker news), `SE` (Stack Exchange) or `reddit` (Reddit).

Every job has a `score` property, which defines the minimum score (or "upvotes" depending on the site) the post must have to be considered.

For **Reddit**, you must also specify a `subreddit`.

For **Stack Exchange**, you must specify a `site` like `stackoverflow` or `tex`. Stack Exchange entries entries can also have a `tags` property to further limit the results to questions with those tags. That way you can only look at `python` questions at stackoverflow for example.

**Hacker News** jobs consider normal stories as well as "Ask HN" and "Show HN" posts by default. But the job can have a `self` property to control this:

| Value of `self` | effect                            |
|-----------------|-----------------------------------|
| Not set         | all stories (links, self and ask) |
| `ask`           | only "Ask HN" stories             |
| `show`          | only "Show HN" stories            |
| `both`          | Ask and Show stories              |


**Searching** can be done with the `keyword` property for Hacker News and Reddit jobs.

You can have multiple jobs for the same site. As an example, if you want all Hacker News stories with a score >=200, but also want to see those mentioning "physics" that are >=20 and all "Ask HN" over 50, an example `jobs.json` would look like:

	[
	  {
	    "type": "HN",
	    "score": 200
	  },
	  {
	    "type": "HN",
	    "keyword": "physics",
	    "score": 20
	  },
	  {
	    "type": "HN",
	    "self": "ask",
	    "score": 50
	  }
	]

The web interface groups posts by subreddit and Stack Exchange Site (HN is its own category). They are sorted from newest to older. Clicking the green arrow on the left will mark that post and every one below it (everything older) in the same group as read. Those will not show up next time.

## Stack Exchange API setup
Stack Exchange requires the app to be authorized by the user to increase its API limits. Dampy does **not** not use this authentification to access *any* user data. But there is no way to authenticate without this access.

To authenticate, go to [https://stackexchange.com/oauth/dialog?client_id=8691&scope=no_expiry&redirect_uri=https://stackexchange.com/oauth/login_success](this) site and accept. You'll be redirected to another site. From its url, copy the string after `access_token=` into the `se_access_token` value in `secrets.json`.

## Philosophy and design
The entire program was designed with simplicity in mind, allowing for easy extension and customization. The interfaces for the three supported sites are defined in files only ~100 lines each, and the main program is about ~200. This should make support for other sites simple.

The posts are stored in a straightforward SQLite database which is used to populate a Flask web interface. The interface uses an easily modified Jinja2 template and css file.

## Todo
- jobs.json file per command line argument
- clear old entries by some logic
- h1-h3 css styling
- pip
- production use with interval scraping