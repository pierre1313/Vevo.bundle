# -*- coding: utf-8 -*-

from PMS import *
from PMS.Objects import *
from PMS.Shortcuts import *
import pyamf, re
from pyamf.remoting.client import RemotingService
from uuid import uuid4

####################################################################################################

# VEVO
VEVO_TITLE_INFO            = 'http://videoplayer.vevo.com/VideoService/AuthenticateVideo?isrc=%s&authToken=%s'

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

FEEDBASE = "http://www.vevo.com"

MRSS  = {'media':'http://search.yahoo.com/mrss/'}
RTE   = {'rte':'http://www.rte.ie/schemas/vod'}

CACHE_TIME = 3600

####################################################################################################

def Start():

    Plugin.AddPrefixHandler(VIDEO_PREFIX, MainMenu, L('Title'), ICON, ART)

    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    MediaContainer.art = R(ART)
    MediaContainer.title1 = NAME
    DirectoryItem.thumb = R(ICON)

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
    
#Navigation

def MainMenu():

    dir = MediaContainer(viewGroup="List")
    dir.Append(Function(DirectoryItem(VideosSubMenu,"Videos")))
    dir.Append(Function(DirectoryItem(ArtistsSubMenu,"Artists")))
    dir.Append(Function(DirectoryItem(GenresSubMenu,"Genres")))
    dir.Append(Function(DirectoryItem(RSS_Channel_parser,"Channels"),pageurl = FEEDBASE + "/channels"))
    dir.Append(Function(InputDirectoryItem(RSS_Search_parser,"Search...",""),pageurl = FEEDBASE + "/search?q="))

    return dir

def VideosSubMenu(sender):
    dir = MediaContainer(title2="Videos", viewGroup="List")

    dir.Append(Function(DirectoryItem(RSS_parser,"Most Viewed today"),pageurl = FEEDBASE + "/videos" + "?order=MostViewedToday"))
    dir.Append(Function(DirectoryItem(RSS_parser,"Most Viewed this week"),pageurl = FEEDBASE + "/videos" + "?order=MostViewedThisWeek"))
    dir.Append(Function(DirectoryItem(RSS_parser,"Most Viewed this month"),pageurl = FEEDBASE + "/videos" + "?order=MostViewedThisMonth"))
    dir.Append(Function(DirectoryItem(RSS_parser,"All Times Most Viewed"),pageurl = FEEDBASE + "/videos" + "?order=MostViewedAllTime"))
    dir.Append(Function(DirectoryItem(RSS_parser,"Recently Added"),pageurl = FEEDBASE + "/videos" + "?order=MostRecent"))
    
    return dir

def ArtistsSubMenu(sender):
    dir = MediaContainer(title2="Artists", viewGroup="List")

    dir.Append(Function(DirectoryItem(AllArtistsSubMenu,"All")))
    dir.Append(Function(DirectoryItem(AZArtistsSubMenu,"A to Z")))
   
    return dir

def AllArtistsSubMenu(sender):
    dir = MediaContainer(title2="All Artists", viewGroup="List")

    dir.Append(Function(DirectoryItem(RSS_Artist_parser,"Most Viewed today"),pageurl = FEEDBASE + "/artists" + "?order=MostViewedToday"))
    dir.Append(Function(DirectoryItem(RSS_Artist_parser,"Most Viewed this week"),pageurl = FEEDBASE + "/artists" + "?order=MostViewedThisWeek"))
    dir.Append(Function(DirectoryItem(RSS_Artist_parser,"Most Viewed this month"),pageurl = FEEDBASE + "/artists" + "?order=MostViewedThisMonth"))
    dir.Append(Function(DirectoryItem(RSS_Artist_parser,"All Times Most Viewed"),pageurl = FEEDBASE + "/artists" + "?order=MostViewedAllTime"))
    dir.Append(Function(DirectoryItem(RSS_Artist_parser,"Recently Added"),pageurl = FEEDBASE + "/artists" + "?order=MostRecent"))
               
    return dir

def AZArtistsSubMenu (sender):
    dir = MediaContainer(title2="Artists A to Z", viewGroup="List")

    for Letter in XML.ElementFromURL(FEEDBASE+"/artists/a-z", True, cacheTime = CACHE_TIME).xpath("//ul[@id='romanIndex']/li/a") :
      dir.Append(Function(DirectoryItem(RSS_Artist_parser,Letter.text), pageurl = FEEDBASE + Letter.get('href')))
    return dir

def GenresSubMenu (sender):
    dir = MediaContainer(title2="Genres", viewGroup="List")

    Genres = XML.ElementFromURL(FEEDBASE+"/videos", True, cacheTime = CACHE_TIME).xpath("//select[@id='genre']/option")
    for Genre in Genres :
      dir.Append(Function(DirectoryItem(RSS_parser,Genre.text),pageurl = FEEDBASE + "/genre/"+Genre.get("value")))
    return dir


#Video File Parsing

#def YtPlayVideo(sender, videoId):
#  ytPage = HTTP.Request(YT_VIDEO_PAGE % (videoId), cacheTime = CACHE_TIME)

#  t = re.findall('&t=([^&]+)', ytPage)[0]
#  fmt_list = re.findall('&fmt_list=([^&]+)', ytPage)[0]
#  fmt_list = String.Unquote(fmt_list, usePlus=False)
#  fmts = re.findall('([0-9]+)[^,]*', fmt_list)

#  index = YT_VIDEO_FORMATS.index("1080p")
#  if YT_FMT[index] in fmts:
#    fmt = YT_FMT[index]
#  else:
#    for i in reversed( range(0, index+1) ):
#      if str(YT_FMT[i]) in fmts:
#        fmt = YT_FMT[i]
#        break
#      else:
#        fmt = 5

#  url = YT_GET_VIDEO_URL % (videoId, t, fmt)
#  return Redirect(url)
####################################################################################################

def PlayVideo(sender, vevo_id):
  info = JSON.ObjectFromURL(VEVO_TITLE_INFO % ( vevo_id, str(uuid4()) ))

  try:
    sourceType = info['video']['videoVersions'][0]['sourceType']
    return Redirect(WebVideoItem( GetBrightCoveVideo(id) ))
  except:
    id = info['video']['videoVersions'][0]['id']  
    return Redirect( GetYouTubeVideo(id) )

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

  Log(result)
  Log(result['id'])

  return BC_PLAYER % ( int(result['id']) )

####################################################################################################
                                  
def isLastPage(source):
    try:
      n = XML.ElementFromString(source, True).xpath("//ul[@class='pagination']/li/a[@class='next']")[0]
      return False
    except:
      return True
    
def doubleThumbSize(imagepath):
    try:
        parts = re.split('[&=?]+',imagepath)
        parts[2]=str(int(parts[2])*2)
        parts[4]=str(int(parts[4])*2)        
        return parts[0] + "?" + parts[1]+ "=" + parts[2] + "&" + parts[3]+ "=" + parts[4] + "&crop=auto"
    except:
        return ''

def getHiResImage(imagepath):
    try:
        image = re.split('[?]+',imagepath)[0]
        return image
    except:
        return R(ART)

def concatPage(url,pageNum):
    try:
        if re.search('[?]',url):
            return url +"&page=" + str(pageNum)    
        else:
            return url +"?page=" + str(pageNum)
    except:
        return url +"?page=" + str(pageNum)    
    
def RSS_Artist_parser(sender, pageurl, page=1, replaceParent=False, query=None):
    pageurlconcat = concatPage(pageurl,page)
    feed = (HTTP.Request(pageurlconcat, cacheTime = CACHE_TIME)).decode("utf-8").replace('"alt "','"entry"').replace('"no-left-margin "','"entry"').replace('<li class="">','<li class="entry">').replace('<div class="artistThumbWrapper">','').replace('</div></div>','')
        
    dir = MediaContainer(title2=sender.itemTitle, viewGroup="List", replaceParent=replaceParent)
        
    if page > 1:
      dir.Append(Function(DirectoryItem(RSS_Artist_parser,"Previous Page"),page = page-1,pageurl = pageurl))
      
    for entry in XML.ElementFromString(feed, True).xpath("//li[@class='entry']"):
      title = entry.xpath("./div[@class='listContent']/h4/a")[0].text
      thumb = doubleThumbSize(entry.xpath("./div[@class='listThumb']//img")[0].get('src'))
      nextart = getHiResImage(thumb)
      link = FEEDBASE + entry.xpath("./div[@class='listThumb']/a")[0].get('href')
      dir.Append(Function(DirectoryItem(RSS_parser,title,thumb=thumb),pageurl = link,backgnd_art=nextart))
      
    if isLastPage(feed) == False:
      dir.Append(Function(DirectoryItem(RSS_Artist_parser,"Next Page"),page = page+1,pageurl = pageurl))
       
    return dir

def RSS_Search_Artist_parser(sender, pageurl, page=1, replaceParent=False, query=None):
    pageurlconcat = concatPage(pageurl,page)
    feed = (HTTP.Request(pageurlconcat, cacheTime = CACHE_TIME)).decode("utf-8").replace('"alt "','"entry"').replace('"no-left-margin "','"entry"').replace('<li class="">','<li class="entry">')
        
    dir = MediaContainer(title2=sender.itemTitle, viewGroup="List", replaceParent=replaceParent)
        
    if page > 1:
      dir.Append(Function(DirectoryItem(RSS_Artist_parser,"Previous Page"),page = page-1,pageurl = pageurl))
      
    for artist in XML.ElementFromString(feed, True).xpath("//ul[@class='videoSearch artistSearch list']/li"):
      title = artist.xpath("./div[@class='listContent']/h4/a")[0].text
      thumb = doubleThumbSize(artist.xpath("./div[@class='listThumb']/div/a/img")[0].get('src'))
      link = FEEDBASE + artist.xpath("./div[@class='listThumb']/div/a")[0].get('href')
      dir.Append(Function(DirectoryItem(RSS_Artist_parser,title,thumb=thumb),pageurl = link))
      
    if isLastPage(feed) == False:
      dir.Append(Function(DirectoryItem(RSS_Artist_parser,"Next Page"),page = page+1,pageurl = pageurl))
       
    return dir

def RSS_Channel_parser(sender, pageurl, page=1, replaceParent=False):
    dir = MediaContainer(title2=sender.itemTitle, viewGroup="List", replaceParent=replaceParent)
    pageurlconcat = concatPage(pageurl,page)
    feed = (HTTP.Request(pageurlconcat, cacheTime = CACHE_TIME)).decode("utf-8")

    if page > 1:
      dir.Append(Function(DirectoryItem(RSS_Channel_parser,"Previous Page"),page = page-1,pageurl = pageurl))

    for entry in XML.ElementFromString(feed, True).xpath("//div[@class='content']/ol/li"):
      title = entry.xpath("./div[@class='listContent']/h4/a")[0].text
      thumb = doubleThumbSize(entry.xpath("./div[@class='listThumb']/a/img")[0].get('src'))
      link = FEEDBASE + entry.xpath("./div[@class='listThumb']/a")[0].get('href')
      dir.Append(Function(DirectoryItem(RSS_parser,title,thumb=thumb),pageurl = link))
    
    if isLastPage(feed) == False:
      dir.Append(Function(DirectoryItem(RSS_Channel_parser,"Next Page"),page = page+1,pageurl = pageurl))
      
    return dir
   
def RSS_Search_parser(sender, pageurl, page=1, query=None, replaceParent=False):
    dir = MediaContainer(title2=sender.itemTitle, viewGroup="List", replaceParent=replaceParent)
    query = query.replace(' ','+')
    dir.Append(Function(DirectoryItem(RSS_Search_Artist_parser,"Search Artists"),pageurl = pageurl+str(query)+"&content=Artists"))
    dir.Append(Function(DirectoryItem(RSS_parser,"Search Videos"),pageurl = pageurl+str(query)+"&content=videos"))
#    query = query.replace(' ','+')
#    feed = HTTP.Request(pageurl+str(query), cacheTime = CACHE_TIME).replace('"alt "','"entry"').replace('"no-left-margin "','"entry"').replace('<li class="">','<li class="entry">')

#    if page > 1:
#      dir.Append(Function(DirectoryItem(RSS_Search_parser,"Previous Page"),page = page-1,pageurl = pageurl, query=query))

#    for artist in XML.ElementFromString(feed, True).xpath("//ul[@class='videoSearch artistSearch list']/li"):
#      title = artist.xpath("./div[@class='listContent']/h4/a")[0].text
#      thumb = doubleThumbSize(artist.xpath("./div[@class='listThumb']/div/a/img")[0].get('src'))
#      link = FEEDBASE + artist.xpath("./div[@class='listThumb']/div/a")[0].get('href')
#      dir.Append(Function(DirectoryItem(RSS_parser,title,thumb=thumb),pageurl = link))
      
#    for songs in XML.ElementFromString(feed, True).xpath("//ul[@class='videoSearch list']/li"):
#      title = song.xpath("./div[@class='listContent']/h4/a")[0].text
#      desc = song.xpath("./div[@class='listContent']/h5/a")[0].text
#      artistbkgnd = FEEDBASE + song.xpath("./div[@class='listContent']/h5/a")[0].get('href')

#      artistart = getHiResImage(XML.ElementFromURL(artistbkgnd, True, cacheTime = CACHE_TIME).xpath("//div[@class='profileImage']/img")[0].get('src'))

#      thumb = doubleThumbSize(song.xpath("./div[@class='listThumb']/img")[0].get('src'))

#      videoId =  song.xpath("./div[@class='listContent']/h4/a")[0].get('rel')
      
#      req = JSON.ObjectFromURL('http://videoplayer.vevo.com/VideoService/AuthenticateVideo?isrc='+videoId)
#      try:
#        videoId = req["video"]["videoVersions"][0]["id"]
      
#        dir.Append(Function(VideoItem(YtPlayVideo,title=title,summary=desc,thumb=thumb,art=artistart),videoId=videoId))
#      except:
#        link = FEEDBASE + song.xpath("./div[@class='listThumb']/a")[0].get('href').replace('&playerType=embedded','').replace('autoplay=0','')
#        url = XML.ElementFromURL(link, True, cacheTime = CACHE_TIME).xpath("//link[@rel='video_src']")[0].get('href')
#        dir.Append(WebVideoItem(url=url,title=title,summary=desc,thumb=thumb))
      
#    if isLastPage(feed) == False:
#      dir.Append(Function(DirectoryItem(RSS_Search_parser,"Next Page"),page = page+1,pageurl = pageurl, query=query))

       
    return dir

def RSS_parser(sender, pageurl, page=1, backgnd_art=R(ART), replaceParent=False, query=None):
    dir = MediaContainer(title2=sender.itemTitle, viewGroup="List", art=backgnd_art, replaceParent=replaceParent)
    pageurlconcat = concatPage(pageurl,page)
    feed = (HTTP.Request(pageurlconcat, cacheTime = CACHE_TIME)).decode("utf-8").replace('"alt "','"entry"').replace('"no-left-margin "','"entry"').replace('<li class="">','<li class="entry">')
    if page > 1:
      dir.Append(Function(DirectoryItem(RSS_parser,"Previous Page"),page = page-1,pageurl = pageurl))

    entries = XML.ElementFromString(feed, True)
    if entries.xpath("//li[@class='entry']") != []:
        for entry in entries.xpath("//li[@class='entry']"):
          title = entry.xpath("./div[@class='listContent']/h4/a")[0].text
          desc = entry.xpath("./div[@class='listContent']/h5/a")[0].text
          artistbkgnd = FEEDBASE + entry.xpath("./div[@class='listContent']/h5/a")[0].get('href')

          artistart = getHiResImage(XML.ElementFromURL(artistbkgnd, True, cacheTime = CACHE_TIME).xpath("//div[@class='profileImage']/img")[0].get('src'))

          thumb = doubleThumbSize(entry.xpath("./div[@class='listThumb']/img")[0].get('src'))

          videoId =  entry.xpath("./div[@class='listContent']/h4/a")[0].get('rel')
      
          #req = JSON.ObjectFromURL('http://videoplayer.vevo.com/VideoService/AuthenticateVideo?isrc='+videoId)
          #try:
          #  videoId = req["video"]["videoVersions"][0]["id"]
      
          #  dir.Append(Function(VideoItem(YtPlayVideo,title=title,summary=desc,thumb=thumb,art=artistart),videoId=videoId))
          #except:
          #  link = FEEDBASE + entry.xpath("./div[@class='listThumb']/a")[0].get('href').replace('&playerType=embedded','').replace('autoplay=0','')
          #  url = XML.ElementFromURL(link, True, cacheTime = CACHE_TIME).xpath("//link[@rel='video_src']")[0].get('href')
          #  dir.Append(WebVideoItem(url=url,title=title,summary=desc,thumb=thumb))
          dir.Append(Function(VideoItem(PlayVideo,title=title,summary=desc,thumb=thumb,art=artistart),vevo_id=videoId))
          
    else:
        for song in entries.xpath("//ul[@class='videoSearch list']/li"):
            title = song.xpath("./div[@class='listContent']/h4/a")[0].text
            desc = song.xpath("./div[@class='listContent']/h5/a")[0].text
            artistbkgnd = FEEDBASE + song.xpath("./div[@class='listContent']/h5/a")[0].get('href')

            artistart = getHiResImage(XML.ElementFromURL(artistbkgnd, True, cacheTime = CACHE_TIME).xpath("//div[@class='profileImage']/img")[0].get('src'))
        
            thumb = doubleThumbSize(song.xpath("./div[@class='listThumb']/img")[0].get('src'))

            videoId =  song.xpath("./div[@class='listContent']/h4/a")[0].get('rel')
      
            #req = JSON.ObjectFromURL('http://videoplayer.vevo.com/VideoService/AuthenticateVideo?isrc='+videoId)
            #try:
            #    videoId = req["video"]["videoVersions"][0]["id"]
      
            #    dir.Append(Function(VideoItem(YtPlayVideo,title=title,summary=desc,thumb=thumb,art=artistart),videoId=videoId))
            #except:
            #    link = FEEDBASE + song.xpath("./div[@class='listThumb']/a")[0].get('href').replace('&playerType=embedded','').replace('autoplay=0','')
            #    url = XML.ElementFromURL(link, True, cacheTime = CACHE_TIME).xpath("//link[@rel='video_src']")[0].get('href')
            #    dir.Append(WebVideoItem(url=url,title=title,summary=desc,thumb=thumb))        

            dir.Append(Function(VideoItem(PlayVideo,title=title,summary=desc,thumb=thumb,art=artistart),vevo_id=videoId))

    if isLastPage(feed) == False:
      dir.Append(Function(DirectoryItem(RSS_parser,"Next Page"),page = page+1,pageurl = pageurl))
      
    return dir
