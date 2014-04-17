trovebot
============

Tweeting content from the following Trove zones:

* Journals, articles and data sets
* Books
* Pictures, photos, and objects
* Music, sound, and video
* Maps
* Diaries, letters, and archives

See me in action at [@TroveBot](http://twitter.com/trovebot).

For digitised newspapers see [@TroveNewsBot](http://twitter.com/trovenewsbot).

Built using the [Trove API](http://trove.nla.gov.au/general/api), the Twitter API, and the [AlchemyAPI](http://www.alchemyapi.com/).

### Making a bot query

Simply tweet some keywords or a url to TroveBot. If it's a url, TroveBot will use AlchemyAPI to extract keywords from the page.

TroveBot will look across Trove zones to see where there are matches. It'll then choose a zone at random and return the most relevant result.

### Modifying your bot query

To limit your query to a particular zone or format, simply add one of these facets to your tweet:

* #artwork ('Art work' facet in the picture zone) 
* #article (anything in the article zone)
* #chapter ('Article/Book chapter' facet in the article zone)
* #paper ('Article/Conference paper' facet in article zone)
* #report ('Article/Report' facet in article zone)
* #review ('Article/Review' facet in article zone)
* #book (anything in the book zone)
* #proceedings ('Conference Proceedings' facet in book zone)
* #data ('Data set' facet in article zone)
* #map (anything in the map zone)
* #object ('Object' facet in picture zone)
* #periodical ('Periodical', 'Periodical/Journal, magazine, other', 'Periodical/Newspaper' facets in article zone
* #photo ('Photograph' facet in picture zone)
* #picture (anything in picture zone)
* #poster ('Poster, chart, other' facet in picture zone)
* #archives (anything in the archives zone)
* #score ('Printed music' facet in the music zone)
* #sound (anything in the music zone)
* #interview ('Sound/Interview, lecture, talk' facet in the music zone)
* #music ('Sound/Recorded music' facet in the music zone)
* #thesis ('Thesis' facet in the book)
* #video ('Video' facet in music zone)
* #abcrn (limit to ABC Radio National content in music zone)

You can also add the following filters:

* #aus (limit to 'Australian' content)
* #online (limit to content freely available online)

Both of these are very metadata quality dependent, so they mightn't always be accurate.

By default all keywords are required for a match. To change this you can add the #any tag. This will match records that contain *any* of your keywords.

In theory, your 'keywords' could be anything that works in Trove's simple search box. This includes things like fielded searches -- eg creator:("Wragge, Clement"). 

### Random goodness

If you supply a query TroveBot will normally return the most relevant record it can find. If you want to dig deeper, you can include the #luckydip tag to make the bot deliver a random record from the matching results.

If you just want to play around without specifying a query, you can:

* include the tag #luckydip by itself to get a random record from somewhere in Trove
* include one of the facets above by itself to get a random record from that zone/format.

### Examples

* Search for a book matching 'wragge': *@TroveBot wragge #book*
* Search for an Australian thesis related to a wikipedia page: *@TroveBot http://en.wikipedia.org/wiki/Clement_Lindley_Wragge #thesis #aus*
* Search for a random photo available online: *@TroveBot #photo #online*

### Automatic botness

* Several times a day TroveBot will tweet a random item.

Released under CC0 licence.
