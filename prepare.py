"""Compile upstream translations and add desktop-specific messages."""
from pathlib import Path
import polib
import html
from desktop.help_content import GUIDES

ROOT = Path(__file__).resolve().parent
TR = {
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


def prepare():
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
