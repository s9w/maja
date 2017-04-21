# maja
maja collects posts from sites you regularly visit (Reddit, Hacker News, Stack Exchange, 4chan) depending on defined criteria and presents them in a central place. 

## Motivation
Many developers and normal people visit Hacker News, Stack Exchange or Reddit (or even 4chan) daily to keep up to date. Since these sites have a very high number of posts, it's infeasible to read them all, as it's common with RSS feeds from blogs.

With maja, you can define minimum scores, specific keywords and other criteria for each of the sites. Matching posts get fetched in regular intervals, stored in a SQLite database and presented on a simple web interface. This approach is much more time-efficient and will catch things even if you are away for longer periods of time.

## Usage
The **jobs** are read from a `jobs.json` file. The config file contains a list of jobs of types `HN` (Hacker news), `SE` (Stack Exchange), `reddit` (Reddit) or `4chan` (4chan). The posts are stored in a SQLite database file in same folder.

### Reddit
Reddit jobs have a mandatory 'score' property which defines the minimum post score. Also you must specify a `subreddit`. You can also specify a `keyword` string that acts as a full-text search on the title, and the post body in case of self posts. You can also set a `self` property to control how to filter self-posts:

| Value of `self` | effect                            |
|-----------------|-----------------------------------|
| Not set         | all posts                       |
| true            | only self posts                   |
| false           | no self posts                     |


### Stack Exchange
Stack exchange jobs need a `score` property. Also you must specify a `site` string, which can be either the domain name or a short form. Examples: `stackoverflow`, `stackoverflow.com`, `tex.stackexchange.com`.

These jobs can have an optional `tags` property to further limit the results to questions with those tags. Tags are entered as a string. Multiple tags must be separated by semicolons. So `c++;lambda` only includes questions with both 'c++' and 'lambda' tags.

### Hacker News
HN jobs have a `score` property and can have keywords like reddit jobs. Normal stories as well as "Ask HN" and "Show HN" posts are considered by default. This can be controlled by the `self` property:

| Value of `self` | effect                            |
|-----------------|-----------------------------------|
| Not set         | all stories (links, self and ask) |
| `ask`           | only "Ask HN" stories             |
| `show`          | only "Show HN" stories            |
| `both`          | Ask and Show stories              |

### 4chan
Needs a `board` property like `b` or `pol`. Has no `score` but instead a `comments` property which sets a minimum amount of replies since 4chan does not have any upvoting functionality. Searching can be done with the usual `keyword` property, which acts as a full-text search on the first post in the thread.

### combining
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
Stack Exchange requires the app to be authorized by the user to increase its API limits. maja does **not** not use this authentification to access *any* user data. But there is no way to authenticate without this access.

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