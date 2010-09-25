# -*- coding: utf-8 -*-

from PMS import *
from PMS.Objects import *
from PMS.Shortcuts import *
import pyamf, re
from pyamf.remoting.client import RemotingService
from uuid import *

####################################################################################################

# VEVO
VEVO_TITLE_INFO            = 'http://videoplayer.vevo.com/VideoService/AuthenticateVideo?isrc=%s&authToken=%s&domain=http://www.vevo.com'

# YouTube
YT_VIDEO_PAGE              = 'http://www.youtube.com/watch?v=%s'
YT_GET_VIDEO_URL           = 'http://www.youtube.com/get_video?video_id=%s&t=%s&fmt=%d&asv=3'
YT_VIDEO_FORMATS           = ['Standard', 'Medium', 'High', '720p', '1080p']
YT_FMT                     = [34, 18, 35, 22, 37]

# BrightCove
BC_PLAYER_ID               = 105891355001
BC_PUBLISHER_ID            = 62009797001
BC_PLAYER                  = 'http://x.brightcove.com/plex/video.php?publisherId=%d&playerId=%d&videoId=%%d' % (BC_PUBLISHER_ID, BC_PLAYER_ID)

VIDEO_PREFIX = "/video/vevo"
NAME = 'Vevo'
ART  = 'art-default.jpg'
ICON = 'icon-default.png'
SEARCHICON = 'search.png'

FEEDBASE = "http://www.vevo.com"

MRSS  = {'media':'http://search.yahoo.com/mrss/'}
RTE   = {'rte':'http://www.rte.ie/schemas/vod'}

CACHE_TIME = 3600

authToken = str(uuid3(NAMESPACE_URL,"http://vevo.com"))
####################################################################################################

def Start():

    Plugin.AddPrefixHandler(VIDEO_PREFIX, MainMenu, L('Title'), ICON, ART)

    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    MediaContainer.art = R(ART)
    MediaContainer.title1 = NAME
    DirectoryItem.thumb = R(ICON)
    
    HTTP.SetCacheTime(CACHE_1HOUR)

####################################################################################################

def UpdateCache():
    HTTP.PreCache(FEEDBASE + "/videos" + "?order=MostViewedToday", CACHE_TIME)
    HTTP.PreCache(FEEDBASE + "/videos" + "?order=MostViewedThisWeek", CACHE_TIME)
    HTTP.PreCache(FEEDBASE + "/videos" + "?order=MostViewedThisMonth", CACHE_TIME)
    HTTP.PreCache(FEEDBASE + "/videos" + "?order=MostViewedAllTime", CACHE_TIME)
    HTTP.PreCache(FEEDBASE + "/videos" + "?order=MostRecent", CACHE_TIME)

    HTTP.PreCache(FEEDBASE + "/artists" + "?order=MostViewedToday", CACHE_TIME)
    HTTP.PreCache(FEEDBASE + "/artists" + "?order=MostViewedThisWeek", CACHE_TIME)
    HTTP.PreCache(FEEDBASE + "/artists" + "?order=MostViewedThisMonth", CACHE_TIME)
    HTTP.PreCache(FEEDBASE + "/artists" + "?order=MostViewedAllTime", CACHE_TIME)
    HTTP.PreCache(FEEDBASE + "/artists" + "?order=MostRecent", CACHE_TIME)

####################################################################################################
#Navigation

def MainMenu():

    dir = MediaContainer(viewGroup="List")
    dir.Append(Function(DirectoryItem(VideosSubMenu,"Videos")))
    dir.Append(Function(DirectoryItem(ArtistsSubMenu,"Artists")))
    dir.Append(Function(DirectoryItem(GenresSubMenu,"Genres")))
    dir.Append(Function(DirectoryItem(RSS_Artist_parser,"Channels"),pageurl = FEEDBASE + "/channels"))
    dir.Append(Function(InputDirectoryItem(RSS_Search_parser,"Search...","Search", art=R(ART), thumb=R("search.png")),pageurl = FEEDBASE + "/search?q="))

    return dir

####################################################################################################

def VideosSubMenu(sender):
    dir = MediaContainer(title2="Videos", viewGroup="List")

    dir.Append(Function(DirectoryItem(RSS_parser,"Most Viewed today"),pageurl = FEEDBASE + "/videos" + "?order=MostViewedToday"))
    dir.Append(Function(DirectoryItem(RSS_parser,"Most Viewed this week"),pageurl = FEEDBASE + "/videos" + "?order=MostViewedThisWeek"))
    dir.Append(Function(DirectoryItem(RSS_parser,"Most Viewed this month"),pageurl = FEEDBASE + "/videos" + "?order=MostViewedThisMonth"))
    dir.Append(Function(DirectoryItem(RSS_parser,"All Times Most Viewed"),pageurl = FEEDBASE + "/videos" + "?order=MostViewedAllTime"))
    dir.Append(Function(DirectoryItem(RSS_parser,"Recently Added"),pageurl = FEEDBASE + "/videos" + "?order=MostRecent"))
    
    return dir

####################################################################################################

def ArtistsSubMenu(sender):
    dir = MediaContainer(title2="Artists", viewGroup="List")

    dir.Append(Function(DirectoryItem(AllArtistsSubMenu,"All")))
    dir.Append(Function(DirectoryItem(AZArtistsSubMenu,"A to Z")))
   
    return dir

####################################################################################################

def AllArtistsSubMenu(sender):
    dir = MediaContainer(title2="All Artists", viewGroup="List")

    dir.Append(Function(DirectoryItem(RSS_Artist_parser,"Most Viewed today"),pageurl = FEEDBASE + "/artists" + "?order=MostViewedToday"))
    dir.Append(Function(DirectoryItem(RSS_Artist_parser,"Most Viewed this week"),pageurl = FEEDBASE + "/artists" + "?order=MostViewedThisWeek"))
    dir.Append(Function(DirectoryItem(RSS_Artist_parser,"Most Viewed this month"),pageurl = FEEDBASE + "/artists" + "?order=MostViewedThisMonth"))
    dir.Append(Function(DirectoryItem(RSS_Artist_parser,"All Times Most Viewed"),pageurl = FEEDBASE + "/artists" + "?order=MostViewedAllTime"))
    dir.Append(Function(DirectoryItem(RSS_Artist_parser,"Recently Added"),pageurl = FEEDBASE + "/artists" + "?order=MostRecent"))
               
    return dir

####################################################################################################

def AZArtistsSubMenu (sender):
    dir = MediaContainer(title2="Artists A to Z", viewGroup="List")

    for Letter in XML.ElementFromURL(FEEDBASE+"/artists/a-z", True, cacheTime = CACHE_TIME).xpath("//ul[@id='romanIndex']/li/a") :
      dir.Append(Function(DirectoryItem(RSS_Artist_parser,Letter.text), pageurl = FEEDBASE + Letter.get('href'),page = 0))

    return dir
####################################################################################################

def GenresSubMenu (sender):
    dir = MediaContainer(title2="Genres", viewGroup="List")

    Genres = XML.ElementFromURL(FEEDBASE+"/videos", True, cacheTime = CACHE_TIME).xpath("//select[@id='genre']/option")
    for Genre in Genres :
      dir.Append(Function(DirectoryItem(RSS_parser,Genre.text),pageurl = FEEDBASE + "/genre/"+Genre.get("value")))
    return dir

####################################################################################################

#Video File Parsing

def GetTitle(vevo_id):
  try:
    info = JSON.ObjectFromURL(VEVO_TITLE_INFO % ( vevo_id, authToken ), cacheTime=CACHE_1MONTH)
    return info['video']['title']
  except:
    return ''
    
####################################################################################################

def GetArtistName(vevo_id):
	  try:
	    info = JSON.ObjectFromURL(VEVO_TITLE_INFO % ( vevo_id, authToken ), cacheTime=CACHE_1MONTH)
	    name = info['video']['mainArtists'][0]['artistName']
	    return name
	  except:
	    return ''

###################################################################################################

def GetTitleArt(vevo_id, mimetype='image/jpeg'):
  try:
    info = JSON.ObjectFromURL(VEVO_TITLE_INFO % ( vevo_id, authToken ), cacheTime=CACHE_1MONTH)
    art = info['video']['imageUrl'] +'?width=512&height=512&crop=auto'
    image = HTTP.Request(art, cacheTime=CACHE_1MONTH)
    if art[-4:4] == '.png':
      mimetype = 'image/png'
    return DataObject(image, mimetype)
  except:
    return R(ICON)

####################################################################################################

def GetArtistArt(vevo_id, mimetype='image/jpeg'):
  try:
    info = JSON.ObjectFromURL(VEVO_TITLE_INFO % ( vevo_id, authToken ), cacheTime=CACHE_1MONTH)
    art = info['video']['mainArtists'][0]['imageUrl'] +'?width=1280&height=720&crop=auto'
    image = HTTP.Request(art, cacheTime=CACHE_1MONTH)
    if art[-4:4] == '.png':
      mimetype = 'image/png'
    return DataObject(image, mimetype)
  except:
    return R(ART)
    
####################################################################################################

def PlayVideo(sender, vevo_id ):
  info = JSON.ObjectFromURL(VEVO_TITLE_INFO % ( vevo_id, authToken ), cacheTime=CACHE_1MONTH)
  sourceType = info['video']['videoVersions'][0]['sourceType']
  id = info['video']['videoVersions'][0]['id']

  if sourceType == 0:
    return Redirect( GetYouTubeVideo(id) )
  elif sourceType == 1:
    return Redirect(WebVideoItem( GetBrightCoveVideo(id) ))

####################################################################################################

def GetYouTubeVideo(video_id):
  yt_page = HTTP.Request(YT_VIDEO_PAGE % (video_id), cacheTime=1)

  t = re.findall('&t=([^&]+)', yt_page)[0]
  fmt_list = re.findall('&fmt_list=([^&]+)', yt_page)[0]
  fmt_list = String.Unquote(fmt_list, usePlus=False)
  fmts = re.findall('([0-9]+)[^,]*', fmt_list)

  index = YT_VIDEO_FORMATS.index( Prefs.Get('ytfmt') )
  if YT_FMT[index] in fmts:
    fmt = YT_FMT[index]
  else:
    for i in reversed( range(0, index+1) ):
      if str(YT_FMT[i]) in fmts:
        fmt = YT_FMT[i]
        break
      else:
        fmt = 5

  url = YT_GET_VIDEO_URL % (video_id, t, fmt)
  return url

####################################################################################################

def GetBrightCoveVideo(video_id):
  client = RemotingService('http://c.brightcove.com/services/messagebroker/amf?playerId=' + str(BC_PLAYER_ID), user_agent='', client_type=3)
  service = client.getService('com.brightcove.player.runtime.PlayerMediaFacade')
  result = service.findMediaByReferenceId('', BC_PLAYER_ID, video_id, BC_PUBLISHER_ID)

  return BC_PLAYER % ( int(result['id']) )

####################################################################################################
                                  
def isLastPage(source):
    try:
      n = XML.ElementFromString(source, True).xpath("//ul[@class='pagination']/li/a[@class='next']")[0]
      return False
    except:
      return True

####################################################################################################

def GetSquareThumb(imagepath):
	try:
		mimetype='image/jpeg'
		art = re.split('[?]+',imagepath)[0] + '?width=512&height=512&crop=auto'
		image = HTTP.Request(art, cacheTime=CACHE_1MONTH)
		if art[-4:4] == '.png':
			mimetype = 'image/png'
		return DataObject(image, mimetype)
	except:
		return R(ART)

####################################################################################################

def GetHiResImage(imagepath):
	try:
		mimetype='image/jpeg'
		art = re.split('[?]+',imagepath)[0] + '?width=1280&height=720&crop=auto'
		image = HTTP.Request(art, cacheTime=CACHE_1MONTH)
		if art[-4:4] == '.png':
			mimetype = 'image/png'
		return DataObject(image, mimetype)
	except:
		return R(ART)

####################################################################################################

def concatPage(url,pageNum):
    try:
        if re.search('[?]',url):
            return url +"&page=" + str(pageNum)    
        else:
            return url +"?page=" + str(pageNum)
    except:
        return url +"?page=" + str(pageNum)    

####################################################################################################

def GetHTML(pageurl, pagenum):
	pageurlconcat = concatPage(pageurl,pagenum)
	return (HTTP.Request(pageurlconcat, cacheTime = CACHE_TIME)).decode("utf-8")

####################################################################################################

def RSS_Artist_parser(sender, pageurl, page=1, replaceParent=False, query=None):

    dir = MediaContainer(title2=sender.itemTitle,viewGroup="List", replaceParent=replaceParent)

    if page > 1:
      dir.Append(Function(DirectoryItem(RSS_Artist_parser,"Previous Page"),page = page-1,pageurl = pageurl))

    if sender.itemTitle == 'Search Artists':
      context = "//ul[@class='videoSearch artistSearch list']/li"
      delimiter = './'
    elif sender.itemTitle == 'Channels':
      context = "//div[@class='content']/ol/li"
      delimiter = './'
    else:
      context = "//li[@class='entry']"
      delimiter = ''

    if page>0:
		feed = GetHTML(pageurl,page).replace('"alt "','"entry"').replace('"no-left-margin "','"entry"').replace('<li class="">','<li class="entry">')
		for entry in XML.ElementFromString(feed, True).xpath(context):
			title = entry.xpath(delimiter+"div[@class='listContent']/h4/a")[0].text
			imagepath = entry.xpath(delimiter+"div[@class='listThumb']//img")[0].get('src')
			link = FEEDBASE + entry.xpath(delimiter+"div[@class='listThumb']//a")[0].get('href')
			dir.Append(Function(DirectoryItem(RSS_parser,title,thumb=Function(GetSquareThumb, imagepath=imagepath),art=Function(GetHiResImage, imagepath=imagepath)),pageurl = link))
	   	if isLastPage(feed) == False:
			dir.Append(Function(DirectoryItem(RSS_Artist_parser,"Next Page"),page = page+1,pageurl = pageurl))
    else:
    	n=1
    	while True:
			feed = GetHTML(pageurl,n).replace('"alt "','"entry"').replace('"no-left-margin "','"entry"').replace('<li class="">','<li class="entry">').replace('<div class="artistThumbWrapper">','').replace('</div></div>','')
			for entry in XML.ElementFromString(feed, True).xpath(context):
				title = entry.xpath(delimiter+"div[@class='listContent']/h4/a")[0].text
				imagepath = entry.xpath(delimiter+"div[@class='listThumb']//img")[0].get('src')
				link = FEEDBASE + entry.xpath(delimiter+"div[@class='listThumb']//a")[0].get('href')
				dir.Append(Function(DirectoryItem(RSS_parser,title,thumb=Function(GetSquareThumb, imagepath=imagepath),art=Function(GetHiResImage, imagepath=imagepath)),pageurl = link))
			n = n+1
			if isLastPage(feed) == True:
				break

    return dir

####################################################################################################

def RSS_Search_parser(sender, pageurl, page=1, query=None, replaceParent=False):
    dir = MediaContainer(title2=sender.itemTitle,viewGroup="List", replaceParent=replaceParent)
    query = query.replace(' ','+')
    dir.Append(Function(DirectoryItem(RSS_Artist_parser,"Search Artists"),pageurl = pageurl+str(query)+"&content=Artists"))
    dir.Append(Function(DirectoryItem(RSS_parser,"Search Videos"),pageurl = pageurl+str(query)+"&content=videos"))

    return dir

####################################################################################################

def RSS_parser(sender, pageurl, page=1, replaceParent=False, query=None):
    dir = MediaContainer(title2 = sender.title2, viewGroup="List", art=sender.art, replaceParent=replaceParent)

    feed = GetHTML(pageurl,page).replace('"alt "','"entry"').replace('"no-left-margin "','"entry"').replace('<li class="">','<li class="entry">')

    if page > 1:
      dir.Append(Function(DirectoryItem(RSS_parser,"Previous Page",art=sender.art),page = page-1,pageurl = pageurl))

    if sender.title2 == "Search...":
      context = "//ul[@class='videoSearch list']/li"
      displayArtist = True
    elif sender.title2 == "Channels" :
      context = "//ul[@class='videoSearch list']/li"
      displayArtist = False
    else:
      context = "//li[@class='entry']"
      if (sender.title2 == "Videos") | (sender.title2 == "Genres"):
        displayArtist = True
      else:
        displayArtist = False

    for entry in XML.ElementFromString(feed, True).xpath(context):
      videoId =  entry.xpath("./div[@class='listContent']/h4/a")[0].get('rel') 
      title = GetTitle(videoId) 
      if title != '':
      	desc = ''
      	if displayArtist == True:
      		title = title + " - " + GetArtistName(videoId)
      	if (sender.art == R(ART)) | (sender.art == None):
       		dir.Append(Function(VideoItem(PlayVideo,title=title,summary=desc,thumb=Function(GetTitleArt, vevo_id=videoId),art=Function(GetArtistArt, vevo_id=videoId)),vevo_id = videoId))
      	else:
      		dir.Append(Function(VideoItem(PlayVideo,title=title,summary=desc,thumb=Function(GetTitleArt, vevo_id=videoId),art=sender.art),vevo_id = videoId))
   
    if isLastPage(feed) == False:
      dir.Append(Function(DirectoryItem(RSS_parser,"Next Page",art=sender.art),page = page+1,pageurl = pageurl))
     
    if len(dir) == 0:
		return MessageContainer('No Results','No video file could be found')
		
    return dir

####################################################################################################
