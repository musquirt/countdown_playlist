import rb, gtk, rhythmdb, random, string, copy

# @TODO: Get a working icon. Create GUI. Turn off repeat.

ui_string = \
"""<ui> 
  <toolbar name="ToolBar"> 
    <placeholder name="CountdownPlaylistPlaceholder" >
        <toolitem name="Countdown Playlist" action="CountdownPlaylist" />
    </placeholder>
  </toolbar>
</ui>"""

class CountdownPlaylist (rb.Plugin):
    def __init__(self):
        rb.Plugin.__init__(self)

    def activate(self, shell):
        icon_file_name = "/usr/share/rhythmbox/icons/hicolor/scalable/places/playlist.svg"
        iconsource = gtk.IconSource()
        iconsource.set_filename(icon_file_name)
        iconset = gtk.IconSet()
        iconset.add_source(iconsource)
        iconfactory = gtk.IconFactory()
        iconfactory.add("mybutton", iconset)
        iconfactory.add_default()
        
        action = gtk.Action("CountdownPlaylist", "CountdownPlaylist",
                            "Create a playlist for a set period of time",
                            "mybutton");
        action.connect("activate", self.countdown_playlist, shell)
        self.action_group = gtk.ActionGroup('CountdownPlaylistActionGroup')
        self.action_group.add_action(action)
        
        ui_manager = shell.get_ui_manager()
        ui_manager.insert_action_group(self.action_group, 0)
        self.UI_ID = ui_manager.add_ui_from_string(ui_string)
        ui_manager.ensure_update();
    
    def deactivate(self, shell):
        ui_manager = shell.get_ui_manager()
        ui_manager.remove_ui(self.UI_ID)
        ui_manager.ensure_update();
    
    ## this is what actually gets called when we click our button ##
    def countdown_playlist(self, event, shell):
        def createSuitablePlaylist(theList, Duration):
            tempList = copy.copy(theList)
            manList = []
            attempts = 0
            while Duration >= 30:
                randomSong = int(random.random() * len(tempList))
                theSongInfo = tempList[randomSong]
                manList.append( theSongInfo )
                Duration = Duration - theSongInfo[1]
                if Duration < -30:
                    ## we're going to try to keep the list close to ##
                     #   +- 30 seconds, but we're not failing more  #
                     #    than 10 times so as not to waste cycles   #
                    attempts = attempts + 1
                    if attempts < 10 and len(manList):
                        manList.pop()
                        Duration = Duration + theSongInfo[1] ## correct for above
                        retries = attempts
                        if attempts > len(manList):
                            retries = len(manList)
                        for i in range(0, retries):
                            tempInfo = manList.pop()
                            Duration = Duration + tempInfo[1]
                            tempList.append(tempInfo)
                else:
                    tempList.pop(randomSong)
                ## Unfortunately RB won't add songs to the ##
                 # queue more than once, so we have to stop here #
                if not len(tempList):
                    #tempList = copy.copy(theList)
                    return manList
            return manList
        
        def addTracksToQueue(shell, theList):
            for track in theList:
                shell.add_to_queue(track[0])
        
        def ClearQueue(shell):
            for row in shell.props.queue_source.props.query_model:
                entry = row[0]
                shell.remove_from_queue(shell.props.db.entry_get(entry, \
                                    rhythmdb.PROP_LOCATION))
        
        def CreateGuiGetInfo():
            keyword = ""
            dur = []
            dialog = gtk.Dialog("CountdownPlaylist Specs", None, 0,
                                (gtk.STOCK_OK, gtk.RESPONSE_YES,
                                gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
                                
            entryKeyword = gtk.Entry()
            labelKeyword = gtk.Label("Keyword (Artist, Genre, Album, Title, etc): ")
            
            entryHour = gtk.Entry()
            labelDuration = gtk.Label("Duration (hour min sec): ")
            
            entryKeyword.set_editable(1)
            entryHour.set_editable(1)
            entryHour.set_size_request(50, 25)
            entryMinute = gtk.Entry()
            entryMinute.set_editable(1)
            entryMinute.set_max_length(6)
            entryMinute.set_size_request(50, 25)
            entrySecond = gtk.Entry()
            entrySecond.set_editable(1)
            entrySecond.set_max_length(9)
            entrySecond.set_size_request(50, 25)
            
            dialog.vbox.pack_start(labelKeyword)
            labelKeyword.show()
            dialog.vbox.pack_start(entryKeyword)
            entryKeyword.show()
            dialog.vbox.pack_start(labelDuration)
            labelDuration.show()
            
            box1 = gtk.HBox(gtk.FALSE, 0)
            dialog.vbox.pack_start(box1)
            box1.show()
            
            labelHour = gtk.Label("h")
            labelMinute = gtk.Label("m")
            labelSecond = gtk.Label("s")
            
            box1.pack_start(entryHour)
            entryHour.show()
            box1.pack_start(labelHour)
            labelHour.show()
            box1.pack_start(entryMinute)
            entryMinute.show()
            box1.pack_start(labelMinute)
            labelMinute.show()
            box1.pack_start(entrySecond)
            entrySecond.show()
            box1.pack_start(labelSecond)
            labelSecond.show()
            response = dialog.run()
            keyword = entryKeyword.get_text()
            for i in range(0, 3):
                dur.append("0")
            if entryHour.get_text():
                dur[0] = entryHour.get_text()
            if entryMinute.get_text():
                dur[1] = entryMinute.get_text()
            if entrySecond.get_text():
                dur[2] = entrySecond.get_text()
            dialog.destroy()
            while gtk.events_pending():
                gtk.main_iteration(False)
            if response is gtk.RESPONSE_CANCEL:
                return (0, 0)
            else:
                return (keyword, dur)
        
        def ConvertInputToDur(dur):
            durSecs = 0
            if dur[0].isdigit():
                durSecs = durSecs + int(dur[0])*3600
            if dur[1].isdigit():
                durSecs = durSecs + int(dur[1])*60
            if dur[2].isdigit():
                durSecs = durSecs + int(dur[2])
            print durSecs
            return durSecs
        
        (ReqKeyword, ReqDur) = CreateGuiGetInfo()
        RequestedDuration = ConvertInputToDur(ReqDur)
        if not RequestedDuration:
            return
        
        ## find all songs that correspond to the request ##
         # on another note, if the request is blank, we  #
         # will just create a playlist using every song  #
        CountdownList = []
        if ReqKeyword:
            for row in shell.props.library_source.props.base_query_model:
                 entry = row[0]
                 ReqKeyword = string.lower(ReqKeyword)
                 artist = string.lower(shell.props.db.entry_get(entry, rhythmdb.PROP_ARTIST))
                 genre  = string.lower(shell.props.db.entry_get(entry, rhythmdb.PROP_GENRE))
                 title  = string.lower(shell.props.db.entry_get(entry, rhythmdb.PROP_TITLE))
                 album  = string.lower(shell.props.db.entry_get(entry, rhythmdb.PROP_ALBUM))
                 album_artist  = string.lower(shell.props.db.entry_get(entry, rhythmdb.PROP_ALBUM_ARTIST))
                 comment  = string.lower(shell.props.db.entry_get(entry, rhythmdb.PROP_COMMENT))
                 year  = shell.props.db.entry_get(entry, rhythmdb.PROP_YEAR)
                 if string.find(artist, ReqKeyword) is not -1 or string.find(genre, ReqKeyword) is not -1 or \
                        string.find(title, ReqKeyword) is not -1 or string.find(album, ReqKeyword) is not -1 or \
                        string.find(album_artist, ReqKeyword) is not -1 or string.find(comment, ReqKeyword) is not -1 \
                        or string.find(string.lower(str(year)), ReqKeyword) is not -1:
                    songLocation = shell.props.db.entry_get(entry, \
                                    rhythmdb.PROP_LOCATION)
                    songDuration = shell.props.db.entry_get(entry, \
                                     rhythmdb.PROP_DURATION)
                    CountdownList.append([songLocation, songDuration])
        if not ReqKeyword or not CountdownList:
            for row in shell.props.library_source.props.base_query_model:
                entry = row[0]
                songLocation = shell.props.db.entry_get(entry, rhythmdb.PROP_LOCATION)
                songDuration = shell.props.db.entry_get(entry, rhythmdb.PROP_DURATION)
                CountdownList.append([songLocation, songDuration])
        
        CountdownList = createSuitablePlaylist(CountdownList, RequestedDuration)
        ClearQueue(shell)
        addTracksToQueue(shell, CountdownList)
        shell.props.shell_player.pause()
        shell.props.shell_player.set_playing_source( shell.props.queue_source )
        shell.props.shell_player.playpause()


