import Grader from "./Grader";

const OUTCOMES = [
  {
    code: "Ç1",
    name: "Karmaşık mühendislik problemlerini çözme becerisi",
    questions: "S1, S4",
    students: 312,
    earned: "4.867",
    total: "6.240",
    pct: 78,
    attained: true,
  },
  {
    code: "Ç2",
    name: "Algoritma tasarımı ve uygulama",
    questions: "S2",
    students: 312,
    earned: "2.652",
    total: "3.120",
    pct: 85,
    attained: true,
  },
  {
    code: "Ç3",
    name: "Veri yapılarını seçme ve kullanma",
    questions: "S3, S5",
    students: 312,
    earned: "2.049",
    total: "4.992",
    pct: 41,
    attained: false,
  },
];

export default function Home() {
  return (
    <>
      <div className="wrap">
        <header className="site-header">
          <div className="logo">
            <span className="logo-mark" aria-hidden="true" /> Rubrik
          </div>
          <nav className="site-nav">
            <a className="nav-link" href="#nasil">
              Nasıl çalışır
            </a>
            <a className="nav-link" href="#akreditasyon">
              Akreditasyon
            </a>
            <a className="nav-link" href="#kvkk">
              Veri güvenliği
            </a>
            <a className="btn btn-ghost" href="#demo">
              Demo isteyin
            </a>
          </nav>
        </header>

        {/* HERO — tez, ürünün kendi ekranıyla anlatılıyor */}
        <div className="hero">
          <div className="hero-copy">
            <p className="eyebrow">
              Mühendislik fakülteleri ve meslek yüksekokulları için
            </p>
            <h1>
              Kağıtları okumayı bize bırakın. <em>Son sözü siz söyleyin.</em>
            </h1>
            <p className="hero-sub">
              El yazısını okur, sizin rubriğinize göre puanlar, verdiği her puanın
              gerekçesini yazar. Notu transkripte işleyen tek kişi hâlâ sizsiniz.
            </p>
            <div className="hero-actions">
              <a className="btn btn-primary" href="#demo">
                Kendi sınavınızla deneyin
              </a>
              <a className="btn btn-ghost" href="#nasil">
                Nasıl çalıştığını görün
              </a>
            </div>
            <p className="hero-note">
              Açık uçlu sorular · kod · formül · şekil — optik form değil.
            </p>
          </div>

          <Grader />
        </div>
      </div>

      {/* PROBLEM */}
      <section>
        <div className="wrap">
          <div className="section-head">
            <p className="eyebrow">Sorun</p>
            <h2>Vize haftası bir hafta sonunu yutuyor.</h2>
            <p>
              Yüzlerce açık uçlu kağıt, tek tek okunacak. Kırkıncı kağıtta verdiğiniz
              puanla ikiyüzüncüde verdiğiniz aynı mı? Kimse emin değil — ve kimse
              kontrol edemiyor.
            </p>
          </div>

          <div className="stats">
            <div className="stat">
              <div className="n">312</div>
              <div className="t">
                Tek bir vizede okunacak kağıt — orta ölçekli bir bölüm için.
              </div>
            </div>
            <div className="stat">
              <div className="n">~26 sa</div>
              <div className="t">Kağıt başına 5 dakikadan, elle okuma süresi.</div>
            </div>
            <div className="stat">
              <div className="n">0</div>
              <div className="t">
                Öğrencinin &ldquo;neden bu puanı aldım&rdquo; sorusuna yazılı cevap.
              </div>
            </div>
            <div className="stat">
              <div className="n">Her dönem</div>
              <div className="t">
                MÜDEK / MEDEK için soru&ndash;kazanım eşleştirmesi, elle, Excel&rsquo;de.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* NASIL ÇALIŞIR — gerçek bir sıra olduğu için numaralandırma hak edilmiş */}
      <section id="nasil">
        <div className="wrap">
          <div className="section-head">
            <p className="eyebrow">Nasıl çalışır</p>
            <h2>Üç adım. Üçüncüsü size ait.</h2>
          </div>

          <div className="flow">
            <div className="step">
              <div className="num">ADIM 1</div>
              <h3>Tarayın</h3>
              <p>
                Telefonla kağıdın fotoğrafını çekin. Uygulama köşeleri bulur,
                perspektifi düzeltir, gölgeyi temizler. Amfide internet yoksa cihazda
                bekler, bağlantı gelince kendi gönderir.
              </p>
            </div>
            <div className="step">
              <div className="num">ADIM 2</div>
              <h3>Okusun ve puanlasın</h3>
              <p>
                El yazısını dijital metne çevirir. Sonra rubriğinizdeki her kriteri tek
                tek gezer, kısmi puanları hesaplar ve <b>neden</b> o puanı verdiğini
                yazar. Tahmin değil, gerekçe.
              </p>
            </div>
            <div className="step">
              <div className="num">ADIM 3</div>
              <h3>Onaylayın</h3>
              <p>
                Solda kağıdın aslı, sağda öneri ve gerekçesi. Katılıyorsanız tek tuş.
                Katılmıyorsanız puanı değiştirirsiniz — sizin notunuz kayda geçer, yapay
                zekânınki değil.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* AKREDİTASYON — kazanım analizi + Excel kanıt dosyası */}
      <section id="akreditasyon">
        <div className="wrap">
          <div className="split">
            <div>
              <p className="eyebrow">Akreditasyon</p>
              <h2>Kazanım kanıt dosyası, dönem sonunda kendiliğinden hazır.</h2>
              <p>
                Her soruyu bir program çıktısına (kazanıma) bağlarsınız. Sistem, o
                çıktıya bağlı tüm soruların <b>onaylanmış</b> puanlarından sınıfın edinim
                oranını hesaplar ve Excel olarak dışa aktarır. Denetçi geldiğinde
                tabloları elle doldurmazsınız — dosya zaten derlenmiş durumda.
              </p>

              <div className="accred">
                <span className="acc">
                  <b>MÜDEK</b> Mühendislik fakülteleri
                </span>
                <span className="acc">
                  <b>MEDEK</b> Meslek yüksekokulları
                </span>
                <span className="acc">
                  <b>FEDEK</b> Fen&ndash;Edebiyat
                </span>
                <span className="acc">
                  <b>YÖKAK</b> Kurumsal dış değerlendirme
                </span>
              </div>

              <ul>
                <li>Soru&ndash;kazanım eşleştirmesi rubriği hazırlarken, bir kez yapılır.</li>
                <li>
                  Edinim oranı yalnızca <b>onaylanmış</b> notlardan hesaplanır. Yapay
                  zekânın önerdiği ama onaylanmamış puan rapora girmez.
                </li>
                <li>
                  Excel&rsquo;in ikinci sayfası &ldquo;bu sayı nasıl çıktı&rdquo;
                  sorusunu cevaplar — denetçinin ilk sorduğu soru budur.
                </li>
                <li>
                  Hiçbir kazanıma bağlanmamış sorular sessizce yutulmaz; raporda uyarı
                  olarak listelenir.
                </li>
              </ul>
            </div>

            {/* Gerçek Excel çıktısının önizlemesi */}
            <div className="panel">
              <div className="panel-bar">
                <span className="panel-file">
                  <span className="xlsx-chip">XLSX</span>
                  BMG101_Vize_kazanim_raporu.xlsx
                </span>
                <span className="sheet-tabs">
                  <span className="sheet-tab on">Kazanım Özeti</span>
                  <span className="sheet-tab">Yöntem</span>
                </span>
              </div>

              <div className="grid-scroll">
                <div className="grid-head">
                  <span>Kod</span>
                  <span>Program Çıktısı</span>
                  <span className="num">Alınan</span>
                  <span className="num">Toplam</span>
                  <span style={{ textAlign: "right" }}>Edinim</span>
                </div>

                {OUTCOMES.map((o) => (
                  <div className="grid-row" key={o.code}>
                    <span className="code">{o.code}</span>
                    <span className="desc">
                      {o.name}
                      <small>
                        {o.questions} · {o.students} kağıt
                      </small>
                    </span>
                    <span className="num">{o.earned}</span>
                    <span className="num">{o.total}</span>
                    <span className={`pill ${o.attained ? "ok" : "no"}`}>
                      %{o.pct} {o.attained ? "EDİNİLDİ" : "EDİNİLMEDİ"}
                    </span>
                  </div>
                ))}
              </div>

              <div className="panel-foot">
                Ç3&rsquo;te sınıfın yarısından fazlası zorlanmış. Bu, gelecek dönem
                müfredatta neyin değişmesi gerektiğini söyleyen bir sinyal — denetim
                için doldurulan bir kutu değil.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* KVKK */}
      <section id="kvkk">
        <div className="wrap">
          <div className="split">
            <div className="shield">
              <div className="lane">
                <span className="badge ok">EVET</span>
                <span>
                  Model <b>sizin sunucunuzda</b> çalışır. Kağıt binadan çıkmaz.
                </span>
              </div>
              <div className="lane">
                <span className="badge ok">EVET</span>
                <span>Veriler Türkiye sınırlarındaki veri merkezinde barınır.</span>
              </div>
              <div className="lane">
                <span className="badge ok">EVET</span>
                <span>Dosyalar diskte ve ağda AES-256 ile şifrelenir.</span>
              </div>
              <div className="lane blocked">
                <span className="badge no">HAYIR</span>
                <span>
                  Öğrenci kağıtları hiçbir dış yapay zekâ servisine gönderilmez.
                </span>
              </div>
              <div className="lane blocked">
                <span className="badge no">HAYIR</span>
                <span>Hiçbir öğrenci verisi model eğitiminde kullanılmaz.</span>
              </div>
            </div>

            <div>
              <p className="eyebrow">KVKK · Veri yerelliği</p>
              <h2>Öğrencinin kağıdı hassas veridir. Öyle davranıyoruz.</h2>
              <p>
                Sınav kağıdı ve not bilgisi 6698 sayılı kanun kapsamında hassas veri
                statüsündedir. Bu yüzden modeli buluta göndermiyoruz — modeli{" "}
                <b>kurumun kendi donanımına</b> kuruyoruz.
              </p>
              <p style={{ marginTop: "1rem" }}>
                Rol bazlı erişim, araştırma görevlisi ile bölüm başkanının ve
                akreditasyon denetçisinin ne görebileceğini kesin çizgilerle ayırır.
                Denetçi tek tek öğrenci notlarını göremez; yalnızca kazanım
                istatistiğini görür.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* İNSAN ONAYI — sayfanın ahlaki merkezi */}
      <section>
        <div className="wrap">
          <div className="oath">
            <div className="rule" />
            <h2>Yapay zekâ not vermez. Not önerir.</h2>
            <p>
              Sistem hiçbir puanı doğrudan transkripte işlemez. Her not, bir
              akademisyenin onayından geçer. Yapay zekânın verdiği puan da, sizin
              verdiğiniz puan da ayrı ayrı saklanır — dönem sonunda &ldquo;makine ne
              dedi, insan ne karar verdi&rdquo; sorusunun cevabı kayıtlıdır.
            </p>
            <p>
              Bu bir pazarlama vaadi değil, mimari bir kısıt. Onay olmadan not alanı boş
              kalır ve o kağıt akreditasyon raporuna girmez.
            </p>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="cta" id="demo">
        <div className="wrap">
          <h2>Bir sonraki vizeyi bir öğleden sonrada bitirin.</h2>
          <p>
            Kendi sınavınızı ve rubriğinizi getirin. Gerçek kağıtlarınızla, kendi
            sunucunuzda deneyelim.
          </p>
          <div className="hero-actions">
            <a className="btn btn-primary" href="#demo">
              Pilot başvurusu
            </a>
            <a className="btn btn-ghost" href="#nasil">
              Teknik dokümanı indirin
            </a>
          </div>
        </div>
      </section>

      <div className="wrap">
        <footer className="site-footer">
          <span>Rubrik — Yapay zekâ destekli akademik değerlendirme platformu</span>
          <span>KVKK uyumlu · Veriler Türkiye&rsquo;de barınır</span>
        </footer>
      </div>
    </>
  );
}
