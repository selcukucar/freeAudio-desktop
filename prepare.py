"""Compile upstream translations and add desktop-specific messages."""
from pathlib import Path
import polib
import html
from desktop.help_content import GUIDES

ROOT = Path(__file__).resolve().parent
TR = {
    'Playback': 'Oynatma',
    'Library and application': 'Kütüphane ve uygulama',
    'Volume (%)': 'Ses düzeyi (%)',
    'Decrease volume (F5)': 'Sesi azalt (F5)',
    'Increase volume (F6)': 'Sesi artır (F6)',
    'F5: decrease volume  |  F6: increase volume  |  F8: stop / play': 'F5: sesi azalt  |  F6: sesi artır  |  F8: durdur / oynat',
    'Could not change volume. Please try again.': 'Ses düzeyi değiştirilemedi. Lütfen yeniden deneyin.',

    'Version %s is available. Use the update button to download it.': '%s sürümü hazır. Güncelleme düğmesinden indirebilirsiniz.',
    'Download &update %s...': '%s &güncellemesini indir...',
    '&Play last media (F8)': '&Son dinleneni oynat (F8)',
    'Paused: %s': 'Duraklatıldı: %s',
    'Playback will restart after stopping.': 'Durdurma tamamlanınca yeniden oynatılacak.',
    'Playback will remain stopped.': 'Oynatma durdurulmuş olarak kalacak.',
    '&Play / pause / resume': '&Oynat / duraklat / sürdür',
    '&Stop playback (F8)': 'Oynatmayı &durdur (F8)',
    '&Pause / resume playback': 'Oynatmayı d&uraklat / sürdür',
    'Playback stopped': 'Oynatma durduruldu',
    'Current media: %s': 'Geçerli medya: %s',
    'Stopping playback...': 'Oynatma durduruluyor...',
    'Could not stop playback. Please try again.': 'Oynatma durdurulamadı. Lütfen yeniden deneyin.',
    'Playback stopped. Recordings continue independently.': 'Oynatma durduruldu. Kayıtlar bağımsız olarak devam eder.',
    'No media is playing. Open the library to choose media.': 'Medya çalmıyor. Medya seçmek için kütüphaneyi açın.',
    'Download and install update (application restarts)': 'Güncellemeyi indir ve kur (uygulama yeniden başlar)',
    'Download portable update ZIP': 'Taşınabilir güncelleme ZIP dosyasını indir',
    'Download only': 'Yalnızca indir',
    'Open release page': 'Sürüm sayfasını aç',
    'A new version is available: %s': 'Yeni bir sürüm var: %s',
    'Application update': 'Uygulama güncellemesi',
    'Downloading update': 'Güncelleme indiriliyor',
    'Preparing verified download...': 'Doğrulanmış indirme hazırlanıyor...',
    'Download progress': 'İndirme ilerlemesi',
    '&Cancel': '&İptal',
    'Cancelling download...': 'İndirme iptal ediliyor...',
    'Downloading update: %d%%': 'Güncelleme indiriliyor: %%%d',
    'The update could not be downloaded or verified. Please try again later.': 'Güncelleme indirilemedi veya doğrulanamadı. Lütfen daha sonra yeniden deneyin.',
    'The verified update was saved to: %s': 'Doğrulanmış güncelleme şuraya kaydedildi: %s',
    'For portable updates, close the application and preserve your data folder when extracting the new ZIP.': 'Taşınabilir güncellemede uygulamayı kapatın ve yeni ZIP dosyasını açarken data klasörünüzü koruyun.',
    'The update could not be verified. Installation was cancelled.': 'Güncelleme doğrulanamadı. Kurulum iptal edildi.',
    'The installer could not be started. The verified download is kept in your profile updates folder.': 'Kurulum başlatılamadı. Doğrulanmış dosya profilinizdeki updates klasöründe saklanıyor.',
    'Start instant &recording of playing station': 'Dinlenen istasyonun anlık &kaydını başlat',
    'Stop instant &recording': 'Anlık &kaydı durdur',
    'Open recordings &folder': 'Kayıt &klasörünü aç',
    'A recording operation is already in progress.': 'Bir kayıt işlemi zaten devam ediyor.',
    'Instant recording is available for live radio only. Use the download command for podcasts and audio books.':
        'Anlık kayıt yalnızca canlı radyo için kullanılabilir. Podcast ve sesli kitaplar için indirme komutunu kullanın.',
    'Saving recording...': 'Kayıt kaydediliyor...',
    'Connecting to station for recording...': 'Kayıt için istasyona bağlanılıyor...',
    'Recording saved: %s': 'Kayıt kaydedildi: %s',
    'Recording stopped. No audio was received.': 'Kayıt durduruldu. Ses verisi alınamadı.',
    'Could not stop recording. The original file has been retained.': 'Kayıt durdurulamadı. Özgün dosya korundu.',
    'Could not start recording. Check the station connection and recording folder.':
        'Kayıt başlatılamadı. İstasyon bağlantısını ve kayıt klasörünü kontrol edin.',
    'No shortcut': 'Kısayol yok',
    'Unavailable': 'Kullanılamıyor',
    'Use &default shortcut': '&Varsayılan kısayolu kullan',
    'Global shortcut (for example control+alt+shift+r; empty disables):':
        'Genel kısayol (örneğin control+alt+shift+r; boş bırakmak kapatır):',
    'The automatic backup could not be created. Your existing profile was not changed.':
        'Otomatik yedek oluşturulamadı. Mevcut profiliniz değiştirilmedi.',
    'The update check could not be completed. Please try again later.':
        'Güncelleme denetimi tamamlanamadı. Lütfen daha sonra yeniden deneyin.',
    'Settings could not be saved. Check that the profile folder is writable.':
        'Ayarlar kaydedilemedi. Profil klasörüne yazılabildiğini kontrol edin.',
    'A recording is in progress. Stop recording and exit?':
        'Kayıt devam ediyor. Kayıt durdurulup uygulama kapatılsın mı?',
    'Profile &backup and restore': 'Profil &yedekleme ve geri yükleme',
    'Profile backup and restore': 'Profil yedekleme ve geri yükleme',
    'Choose a profile action.': 'Profil işlemini seçin.',
    'Create a backup': 'Yedek oluştur',
    'Restore a backup at next startup': 'Yedeği sonraki açılışta geri yükle',
    'Profile backup': 'Profil yedeği', 'Restore profile': 'Profili geri yükle',
    'Restore settings and libraries from this backup at the next startup? Your current profile will be backed up first.':
        'Bu yedekteki ayarlar ve kitaplıklar sonraki açılışta geri yüklensin mi? Önce mevcut profilinizin yedeği alınacak.',
    'Backup checked. Restart the application to restore it.':
        'Yedek doğrulandı. Geri yüklemek için uygulamayı yeniden başlatın.',
    'Profile backup saved. Recordings, downloads and account credentials are not included.':
        'Profil yedeği kaydedildi. Kayıtlar, indirilen medya ve hesap giriş bilgileri yedeğe dahil değildir.',
    'The profile operation could not be completed.': 'Profil işlemi tamamlanamadı.',
    'The update channel has not been published yet.': 'Güncelleme kanalı henüz yayımlanmadı.',
    '&Resume last media when the application starts': '&Uygulama açıldığında son dinleneni sürdür',
    'Screen reader': 'Ekran okuyucu',
    'Windows voice (SAPI5)': 'Windows sesi (SAPI5)',
    'Windows &voice:': 'Windows &sesi:',
    'Send notifications to a &braille display through the screen reader':
        'Bildirimleri ekran okuyucu üzerinden &braille ekranına gönder',
    'Optional: requires a running NVDA or JAWS screen reader and a connected braille display. The application itself runs independently of the screen reader.':
        'İsteğe bağlıdır: Çalışan NVDA veya JAWS ve bağlı bir braille ekranı gerekir. Uygulamanın kendisi ekran okuyucudan bağımsız çalışır.',
    'Settings were reset. Changes made on the freeAudio settings page before this will not be saved. Restart the application so every setting takes effect.':
        'Ayarlar sıfırlandı. Bu işlemden önce ayarlar sayfasında yapılan değişiklikler kaydedilmeyecek. Tüm ayarların uygulanması için uygulamayı yeniden başlatın.',
    'This shortcut is assigned to another command.': 'Bu kısayol başka bir komuta atanmış.',
    'Settings': 'Ayarlar', 'Error': 'Hata',
    'Radio, podcasts, audio books and local music': 'Radyo, podcast, sesli kitap ve yerel müzik',
    '&Open library': '&Kütüphaneyi aç', '&Settings': '&Ayarlar',
    '&Commands and shortcuts': 'Ko&mutlar ve kısayollar',
    '&Notification history': '&Bildirim geçmişi', '&Language / Dil': '&Dil / Language',
    'Check for &updates': '&Güncellemeleri denetle', '&Help': '&Yardım', 'E&xit': '&Çıkış',
    'Commands and shortcuts': 'Komutlar ve kısayollar', 'Commands': 'Komutlar',
    'Global shortcut (for example control+windows+r; empty disables):':
        'Genel kısayol (örneğin control+windows+r; boş bırakırsanız devre dışı kalır):',
    'Unavailable shortcuts': 'Kullanılamayan kısayollar', '&Run command': 'Komutu ça&lıştır',
    '&Save shortcut': 'Kısayolu &kaydet', '&Close': 'Ka&pat', 'Shortcut saved.': 'Kısayol kaydedildi.',
    'Notification history': 'Bildirim geçmişi', 'Notifications': 'Bildirimler',
    'Choose language. Restart the application to apply.': 'Dili seçin. Uygulamak için uygulamayı yeniden başlatın.',
    'Language saved. Restart the application.': 'Dil kaydedildi. Uygulamayı yeniden başlatın.',
    'No desktop update channel has been configured. This preview does not install NVDA add-on updates.':
        'Masaüstü güncelleme kanalı henüz yapılandırılmadı. Bu önizleme NVDA eklentisi güncellemelerini yüklemez.',
    'No newer release was found.': 'Daha yeni bir sürüm bulunamadı.',
    'A new version is available. Open the download page?': 'Yeni sürüm var. İndirme sayfası açılsın mı?',
    'Some shortcuts are unavailable. Open Commands and shortcuts for details.':
        'Bazı kısayollar kullanılamıyor. Ayrıntılar için Komutlar ve kısayolları açın.',
    'The application is already running.': 'Uygulama zaten çalışıyor.',
}


TR.update({'&Downloads and offline podcasts': 'İ&ndirmeler ve çevrimdışı podcastler', 'Downloads and offline podcasts': 'İndirmeler ve çevrimdışı podcastler', '&Listening history': 'Dinleme &geçmişi', 'Listening history': 'Dinleme geçmişi', '&About freeAudio Desktop': 'freeAudio Desktop &hakkında', 'About freeAudio Desktop': 'freeAudio Desktop hakkında', 'Credits and license': 'Emek, teşekkür ve lisans', 'Original freeAudio NVDA add-on': 'Özgün freeAudio NVDA eklentisi', 'Show': 'Göster', 'All downloads': 'Tüm indirmeler', 'Downloaded episodes': 'İndirilen bölümler', 'Podcast downloads': 'Podcast indirmeleri', 'Download details': 'İndirme ayrıntıları', 'Download progress': 'İndirme ilerlemesi', 'Queued': 'Sırada', 'Downloading': 'İndiriliyor', 'Downloaded': 'İndirildi', 'Cancelled': 'İptal edildi', 'Failed': 'Başarısız', '&Play downloaded episode': 'İndirilen bölümü &oynat', '&Read progress': 'İlerlemeyi &bildir', '&Cancel download': 'İndirmeyi i&ptal et', '&Retry download': 'İndirmeyi &yeniden dene', 'Open download &folder': 'İndirme &klasörünü aç', 'Remove from &list': '&Listeden kaldır', '&Delete downloaded file': 'İndirilen dosyayı &sil', 'Delete downloaded file': 'İndirilen dosyayı sil', '%s of %s MB': '%s / %s MB', '%s MB downloaded; total size unknown': '%s MB indirildi; toplam boyut bilinmiyor', 'The downloaded file is not available': 'İndirilen dosya bulunamıyor', 'Cancelling download...': 'İndirme iptal ediliyor...', 'Download queued': 'İndirme sıraya alındı', 'Delete this downloaded file?\n%s': 'Bu indirilen dosya silinsin mi?\n%s', 'Operation failed: %s': 'İşlem başarısız: %s', 'Recently played media': 'Son dinlenenler', '&Play selected media': 'Seçili medyayı &oynat', 'Clear listening &history': 'Dinleme geçmişini &temizle', 'Clear listening history? Saved media files will be kept.': 'Dinleme geçmişi temizlensin mi? Kaydedilmiş medya dosyaları korunacak.', 'Listening history could not be saved. Playback continues.': 'Dinleme geçmişi kaydedilemedi. Oynatma devam ediyor.', 'Download cancelled: %s': 'İndirme iptal edildi: %s', 'Opening saved media...': 'Kayıtlı medya açılıyor...', 'Saved media could not be opened. Check your account and library.': 'Kayıtlı medya açılamadı. Hesabınızı ve kitaplığınızı kontrol edin.', 'Downloads are in progress. Cancel them and exit?': 'İndirmeler sürüyor. İndirmeler iptal edilip uygulamadan çıkılsın mı?', 'Cancelling downloads before exit...': 'Çıkmadan önce indirmeler iptal ediliyor...'})
TR.update({
    'Recordings folder must be an absolute path.': 'Kayıt klasörü D:\\Kayıtlar gibi tam bir yol olmalıdır.',
    'Recording folder unavailable; recording was not started: %s': 'Kayıt klasörü kullanılamıyor; kayıt başlatılmadı: %s',
})

TR.update({'Podcast': 'Podcast', 'Radio': 'Radyo', 'Audio book': 'Sesli kitap', 'Local music': 'Yerel müzik'})

TR.update({'Previous episode / chapter': 'Önceki bölüm',
 'Next episode / chapter': 'Sonraki bölüm',
 'Start radio recording': 'Radyo kaydını başlat',
 'Stop radio recording': 'Radyo kaydını durdur',
 'Recording continues independently of playback.': 'Oynatma durdurulsa da kayıt devam eder.',
 'Record the playing radio. Select a live station first.': 'Çalan radyoyu kaydeder. Önce bir canlı '
                                                           'radyo açın.',
 'Recording shortcut: %s': 'Kayıt kısayolu: %s',
 'No global recording shortcut is assigned.': 'Genel kayıt kısayolu atanmamış.',
 'Select a podcast episode or audio book chapter first.': 'Önce bir podcast veya sesli kitap '
                                                          'bölümü oynatın.',
 'An episode is already being opened.': 'Bir bölüm zaten açılıyor.',
 'Opening episode / chapter...': 'Bölüm açılıyor...',
 'This episode is not in the downloaded episode list.': 'Bu bölüm indirilen bölümler listesinde '
                                                        'bulunmuyor.',
 'The episode list is unavailable. Select the podcast in the library.': 'Bölüm listesi '
                                                                        'kullanılamıyor. Podcasti '
                                                                        'kütüphaneden seçin.',
 'The current episode was not found in this podcast.': 'Çalan bölüm bu podcastin listesinde '
                                                       'bulunamadı.',
 'The next chapter could not be opened.': 'Kitap bölümü açılamadı.',
 'The audio book is unavailable. Select it in the library.': 'Sesli kitap kullanılamıyor. Kitabı '
                                                             'kütüphaneden seçin.',
 'Command group': 'Komut grubu',
 'Application commands': 'Uygulama komutları',
 'Favourite and library item shortcuts': 'Favori ve kitaplık öğelerinin kısayolları',
 'Release notes': 'Bu sürümdeki yenilikler',
 'Loading release notes...': 'Sürüm notları yükleniyor...',
 'No release notes were provided.': 'Bu sürüm için not eklenmemiş.',
 'Release notes could not be loaded. Download options remain available.': 'Sürüm notları '
                                                                          'yüklenemedi. İndirme '
                                                                          'seçeneklerini '
                                                                          'kullanabilirsiniz.',
 'Update action': 'Güncelleme işlemi'})

TR.update({'Recording shortcut unavailable: %s': 'Kayıt kısayolu kullanılamıyor: %s'})


TR.update({
    '&Continue listening': '&Dinlemeye devam et',
    'Continue listening': 'Dinlemeye devam et',
    '&Sleep timer': '&Uyku zamanlayıcısı',
    'Sleep timer': 'Uyku zamanlayıcısı',
    'Sleep timer (active)': 'Uyku zamanlayıcısı (etkin)',
    'Unfinished podcasts and audio books': 'Yarım kalan podcastler ve sesli kitaplar',
    'Saved listening position': 'Kaydedilen dinleme konumu',
    '&Continue selected media': 'Seçili medyaya &devam et',
    '&Refresh positions': 'Konumları &yenile',
    'No unfinished media yet. Listen to a podcast or audio book first.': 'Henüz yarım kalan medya yok. Önce bir podcast veya sesli kitap dinleyin.',
    'Saved position: %s': 'Kaydedilen konum: %s',
    'This media is unavailable. Check the file or library.': 'Bu medya kullanılamıyor. Dosyayı veya kütüphaneyi kontrol edin.',
    'When': 'Ne zaman',
    'After a duration': 'Belirli bir süre sonra',
    'At the end of this episode / chapter': 'Bu bölümün sonunda',
    'Minutes (1–480)': 'Dakika (1–480)',
    '%d minutes': '%d dakika',
    'Action': 'İşlem',
    'Stop playback': 'Oynatmayı durdur',
    'Shut down the computer': 'Bilgisayarı kapat',
    'Recordings and downloads continue when playback stops. Computer shutdown has a 60-second cancellation warning and is blocked by active recordings or downloads. Other applications are never force-closed.': 'Oynatma durduğunda kayıtlar ve indirmeler devam eder. Bilgisayarı kapatmadan önce iptal için 60 saniye tanınır. Aktif kayıt veya indirme varsa kapatma iptal edilir. Diğer uygulamalar zorla kapatılmaz.',
    'Timer status': 'Zamanlayıcı durumu',
    '&Set timer': 'Zamanlayıcıyı &başlat',
    '&Cancel timer': 'Zamanlayıcıyı &iptal et',
    'Choose between 1 and 480 minutes.': '1 ile 480 arasında dakika seçin.',
    'Play a podcast episode or audio book chapter first.': 'Önce bir podcast veya sesli kitap bölümü oynatın.',
    'Computer shutdown is blocked by active recordings or downloads.': 'Aktif kayıt veya indirme varken bilgisayar kapatılamaz.',
    'Sleep timer set.': 'Uyku zamanlayıcısı ayarlandı.',
    'No sleep timer is active.': 'Etkin uyku zamanlayıcısı yok.',
    'Remaining: %s': 'Kalan süre: %s',
    'Preparing computer shutdown. Cancel is still available.': 'Bilgisayar kapatılmaya hazırlanıyor. Hâlâ iptal edebilirsiniz.',
    'Sleep timer cancelled.': 'Uyku zamanlayıcısı iptal edildi.',
    'End-of-episode sleep timer cancelled because the media changed.': 'Medya değiştiği için bölüm sonu uyku zamanlayıcısı iptal edildi.',
    'Computer shutdown cancelled: a recording or download is active.': 'Bilgisayarı kapatma iptal edildi: aktif kayıt veya indirme var.',
    'The computer will shut down within 60 seconds. Use Cancel timer to stop it.': 'Bilgisayar 60 saniye sonra kapatılacak. Vazgeçmek için Zamanlayıcıyı iptal et düğmesini kullanın.',
    'Sleep timer: playback stopped.': 'Uyku zamanlayıcısı: oynatma durduruldu.',
    'Computer shutdown cancelled because playback did not stop in time.': 'Oynatma zamanında durmadığı için bilgisayarı kapatma iptal edildi.',
    'Computer shutdown cancelled because playback changed or could not be stopped.': 'Oynatma değiştiği veya durdurulamadığı için bilgisayarı kapatma iptal edildi.',
    'Computer shutdown could not be started: %s': 'Bilgisayarı kapatma başlatılamadı: %s',
    'Unlistened episodes': 'Dinlenmemiş bölümler',
    'Listened episodes': 'Dinlenmiş bölümler',
    'Listened': 'Dinlendi',
    'Podcast group': 'Podcast grubu',
    'All podcasts': 'Tüm podcastler',
    'Unknown podcast': 'Podcast adı bilinmiyor',
    'Downloaded files: %d; disk usage: %s MB': 'İndirilen dosya: %d; disk kullanımı: %s MB',
    'Mark as &listened': '&Dinlendi olarak işaretle',
    'Mark as &unlistened': '&Dinlenmedi olarak işaretle',
    'Edit &podcast name': '&Podcast adını düzenle',
    'Podcast name for this episode:': 'Bu bölümün podcast adı:',
    'A library list needed recovery. The original data was kept at: %s': 'Bir kütüphane listesi onarıldı. Önceki veriler şurada korundu: %s',
    'A library list could not be changed safely. Existing data was kept: %s': 'Bir kütüphane listesi güvenle değiştirilemedi. Mevcut veriler korundu: %s',
    'The library is read-only. Restore a compatible profile backup.': 'Kütüphane salt okunur durumda. Uyumlu bir profil yedeği geri yükleyin.',
    'Application window shortcuts': 'Uygulama penceresi kısayolları',
    'Shortcut (empty disables; application window shortcuts work while the main window is active):': 'Kısayol (boş bırakırsanız kapanır; pencere kısayolları ana pencere etkinken çalışır):',
    '&Retry unavailable shortcuts': 'Kullanılamayan kısayolları yeniden &dene',
    'Shortcut registration retried.': 'Kısayollar yeniden kaydedilmeye çalışıldı.',
    'The shortcut is already registered by another application.': 'Kısayol başka bir uygulama tarafından kullanılıyor.',
    'Windows denied permission to register this shortcut.': 'Windows bu kısayolun kaydedilmesine izin vermedi.',
    'Windows could not register this shortcut.': 'Windows bu kısayolu kaydedemedi.',
    'Windows-key combinations cannot be application shortcuts.': 'Windows tuşunu içeren bileşimler pencere kısayolu olarak kullanılamaz.',
    'Open library': 'Kütüphaneyi aç',
    'Language / Dil': 'Dil / Language',
    'Profile backup and restore': 'Profil yedekleme ve geri yükleme',
    'About freeAudio Desktop': 'freeAudio Desktop hakkında',
    'Exit': 'Çıkış',
})


def prepare():
    import shutil
    import wx
    standard = Path(wx.__file__).parent / 'locale/tr/LC_MESSAGES/wxstd.mo'
    target = ROOT / 'locale/tr/LC_MESSAGES/wxstd.mo'
    shutil.copyfile(standard,target)
    source = ROOT / 'locale/tr/LC_MESSAGES/nvda.po'
    catalog = polib.pofile(str(source))
    for original, translated in TR.items():
        entry = catalog.find(original)
        if entry is None:
            entry = polib.POEntry(msgid=original, msgstr=translated)
            catalog.append(entry)
        else:
            entry.msgstr = translated
        entry.flags = [flag for flag in entry.flags if flag != 'fuzzy']
    catalog.save(str(source))
    catalog.save_as_mofile(str(source.with_suffix('.mo')))
    for language, destination in [('tr', ROOT / 'docs/tr/desktop.html'),
                                  ('en', ROOT / 'docs/desktop.html')]:
        sections = GUIDES[language]
        contents = ''.join('<section><h2 id="s' + str(index) + '">' + html.escape(title) +
                           '</h2><p>' + html.escape(body) + '</p></section>'
                           for index, (title, body) in enumerate(sections))
        navigation = '<nav aria-label="Contents"><ul>' + ''.join(
            '<li><a href="#s' + str(index) + '">' + html.escape(title) + '</a></li>'
            for index, (title, body) in enumerate(sections)) + '</ul></nav>'
        document = ('<!doctype html><html lang="' + language + '"><meta charset="utf-8">'
                    '<title>freeAudio Desktop — Help / Yardım</title>'
                    '<meta name="viewport" content="width=device-width,initial-scale=1">'
                    '<style>body{font:1.1rem/1.6 system-ui;max-width:75ch;margin:2rem auto;padding:1rem}'
                    ':focus-visible{outline:3px solid currentColor}section{margin-block:2rem}</style>'
                    '<body><main><h1>freeAudio Desktop</h1>' + navigation + contents + '</main></body></html>')
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(document, encoding='utf-8')


if __name__ == '__main__':
    prepare()
