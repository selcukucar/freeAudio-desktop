"""Permanent acknowledgement of the original work, in both application languages."""
ORIGINAL_URL = 'https://github.com/Surveyor123/freeAudio'


def credits_text(language):
    if language == 'tr':
        return ('Emek ve teşekkür\n\n'
                'freeAudio Desktop, Çağrı Doğan tarafından geliştirilen freeAudio NVDA eklentisi '
                'temel alınarak Selçuk Uçar tarafından bağımsız bir Windows masaüstü uygulamasına '
                'dönüştürülmüş ve geliştirilmiştir. Özgün eklenti ve temelini oluşturan çalışmalar '
                'için Çağrı Doğan’a teşekkür ederiz. Diğer katkıda bulunanların ve kullanılan '
                'bileşenlerin emekleri ile mevcut telif bildirimleri korunmaktadır.\n\n'
                'Uygulama kaynak kodu GNU GPL v2 lisansı altında paylaşılmaktadır. '
                'Üçüncü taraf ses bileşenleri kendi lisanslarına tabidir; LICENSE ve THIRD-PARTY.md '
                'dosyalarına bakınız.\n\nÖzgün eklenti: ' + ORIGINAL_URL)
    return ('Credits and thanks\n\n'
            'freeAudio Desktop was adapted and further developed by Selçuk Uçar as an independent '
            'Windows desktop application, based on the freeAudio NVDA add-on developed by Çağrı Doğan. '
            'We thank Çağrı Doğan for the original add-on and the work on which this application is '
            'built. Existing copyright notices and the contributions of other contributors and '
            'component authors are preserved.\n\n'
            'Application source code is shared under GNU GPL v2. Third-party audio components '
            'have their own licenses; see LICENSE and THIRD-PARTY.md.\n\nOriginal add-on: ' + ORIGINAL_URL)
