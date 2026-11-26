"""Resolve adjacent episodes/chapters without moving focus or starting playback."""
from pathlib import Path


def adjacent_index(index, length, direction, first, last):
    target = index + direction
    if target < 0 or target >= length:
        raise ValueError(first if direction < 0 else last)
    return target


def podcast_target(plugin, station, direction, downloads):
    from freeAudio import podcast
    from .media_dialogs import playback_station
    key = station.get('podcast_resume_key') or station.get('url')
    if Path(station.get('url', '')).is_file():
        items = [x for x in downloads.snapshot() if x['state'] == 'completed' and downloads.resolve_path(x).is_file()]
        index = next((i for i,x in enumerate(items) if x['url'] == key), None)
        if index is None:
            raise ValueError('This episode is not in the downloaded episode list.')
        index = adjacent_index(index,len(items),direction,'Already at first episode','Already at last episode')
        return playback_station(items[index],downloads), None
    dialog = plugin._nav_dialog()
    manager = plugin._nav_podcast_manager()
    feed_url = station.get('podcast_feed_url') or ''
    feed = manager.get_feed_by_url(feed_url) if feed_url else None
    preview = getattr(dialog, '_podcast_preview_feed', None) if dialog else None
    if not feed and preview and preview.url == feed_url:
        feed = preview
    if not feed or not feed.episodes:
        if not feed_url:
            raise ValueError('The episode list is unavailable. Select the podcast in the library.')
        profile = feed.audio_profile if feed else None
        feed, error = podcast.PodcastManager()._fetch_and_parse(feed_url)
        if feed and profile: feed.audio_profile = profile
        if error: raise ValueError(error)
    episodes = list(feed.episodes) if feed else []
    index = next((i for i,ep in enumerate(episodes) if ep.url in (key,station.get('url'))), None)
    if index is None: raise ValueError('The current episode was not found in this podcast.')
    target = episodes[adjacent_index(index,len(episodes),direction,'Already at first episode','Already at last episode')]
    result = target.to_dict()
    result['podcast_feed_url'] = feed.url
    result['podcast_feed_title'] = feed.title
    if feed.author: result['podcast_author'] = feed.author
    if feed.audio_profile: result['station_audio'] = feed.audio_profile
    result['name'] = feed.title + ' — ' + target.title if target.title != feed.title else feed.title
    return result, None


def audiobook_target(station, direction):
    from freeAudio import getem, librivox, gutenberg_audiobooks
    for module, library_type in ((getem,getem.GetemLibrary),(librivox,librivox.LibrivoxLibrary),
                                 (gutenberg_audiobooks,gutenberg_audiobooks.GutenbergLibrary)):
        try:
            library = library_type()
            book = library.get_book_by_key(station.get('getem_detail_url'))
        except Exception:
            continue
        if not book: continue
        index = adjacent_index(int(station.get('getem_chapter_index',0)),len(book.chapters),direction,
                               'Already at first part','Already at last part')
        chapter = book.chapters[index]
        url = module.get_stream_url(chapter['url'],referer=book.detail_url)
        if not url: raise ValueError('The next chapter could not be opened.')
        result = book.to_dict()
        title = chapter.get('title') or book.title
        result.update(url=url,url_resolved=url,podcast_resume_key=chapter['url'],
                      getem_chapter_index=index,audiobook_chapter_title=title,
                      name=book.title + ' — ' + title if title != book.title else book.title)
        if book.audio_profile: result['station_audio'] = book.audio_profile
        return result, lambda: library.mark_progress(book,index)
    raise ValueError('The audio book is unavailable. Select it in the library.')


def adjacent_media(plugin, station, direction, downloads):
    if direction not in (-1,1): raise ValueError('Invalid navigation direction')
    if station.get('media_kind') == 'podcast': return podcast_target(plugin,station,direction,downloads)
    if station.get('media_kind') == 'audiobook': return audiobook_target(station,direction)
    raise ValueError('Select a podcast episode or audio book chapter first.')
