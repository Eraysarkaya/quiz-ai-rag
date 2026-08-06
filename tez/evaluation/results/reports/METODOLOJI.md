# Metodoloji

Bu deney düzeni, soru üretiminde kullanılan büyük dil modelleri arasındaki farkın, geri getirim (retrieval) varyansından olabildiğince ayrıştırılarak gözlemlenebilmesi amacıyla kurulmuştur. Bu nedenle değerlendirme hattı, aynı konu kümesi, aynı ortak bağlam dosyası, aynı üretim hattı ve aynı bağımsız hakem model üzerinden standartlaştırılmıştır.

## 1. Deney Tasarımı

Bu çalışma kapsamında önce `topics.json` dosyasında yer alan 100 adet bilim odaklı konu başlığı sabitlenmiştir. Ardından production retriever kullanılarak her konu için bilgi erişim süreci yalnızca bir kez işletilmiş ve elde edilen bağlamlar `shared_rag_contexts.json` dosyasına kaydedilmiştir. Böylece retrieval çıktıları dondurulmuş ve tüm üretici modellerin aynı bağlam kümesi ile çalıştırılması sağlanmıştır.

Ortak bağlamların oluşturulmasının ardından tüm üretici modeller, aynı production `MCQGenerator` hattı üzerinden değerlendirilmiştir. Bu aşamada her modelden, aynı konu-bağlam eşleşmeleri kullanılarak çoktan seçmeli soru, doğru cevap ve çeldirici seçenekler üretilmesi istenmiştir. Üretim çıktıları tamamlandıktan sonra elde edilen soru kümeleri, üretici modellerden bağımsız bir hakem model olan `GPT-OSS 120B` ile kör değerlendirmeye tabi tutulmuştur. Böylece değerlendirme istemlerinde model adlarına yer verilmemiş ve hakem modelin yalnızca içerik kalitesi üzerinden puanlama yapması hedeflenmiştir.

## 2. Bu Yöntemin Seçilme Gerekçesi

LLM karşılaştırmalarında retrieval bileşeninin modelden modele farklılaşması, gözlenen performans farklarının hangi katmandan kaynaklandığını belirsiz hale getirebilmektedir. Bu nedenle retrieval süreci tekilleştirilmiş ve deney boyunca sabit tutulmuştur. Böylelikle ölçülen farkın, bilgi erişim stratejisinden değil, esas olarak üretici modelin soru kurma, doğru cevap belirleme ve çeldirici üretme yeteneğinden kaynaklandığı kabul edilmiştir.

Bu yaklaşım özellikle tez bağlamında önem taşımaktadır; çünkü amaç, “hangi model daha iyi retrieval yaptı?” sorusundan ziyade, “aynı bağlam verildiğinde hangi model daha kaliteli sınav maddesi üretebildi?” sorusuna yanıt üretmektir.

## 3. Retrieval Yapılandırması

Deneyde kullanılan ortak retrieval yapılandırması aşağıdaki gibidir:

- `top_k = 5`
- `min_score = 0.25`
- değerlendirilen konu sayısı = `100`

Bu ayarlar ile her konu için en fazla beş aday bağlamın değerlendirilmesi ve düşük benzerlikli sonuçların elenmesi amaçlanmıştır. Dondurulmuş ortak bağlam yaklaşımı sayesinde tüm üretici modellerin aynı bilgi temeli üzerinde sınanması sağlanmıştır.

## 4. Değerlendirme Metrikleri

Model karşılaştırması dört temel metrik üzerinden yürütülmüştür:

| Metrik | İyi Eşik | Açıklama |
|---|---:|---|
| question_quality | 0.75 | Sorunun açık, cevaplanabilir ve eğitimsel açıdan anlamlı olup olmadığı |
| answer_correctness | 0.75 | Doğru cevap olarak sunulan seçeneğin olgusal doğruluğu |
| distractor_quality | 0.70 | Çeldiricilerin makul, alan içi ve buna rağmen yanlış olup olmadığı |
| answer_relevancy | 0.75 | Doğru cevabın soruya doğrudan yanıt verip vermediği |

Puanlama `0.0` ile `1.0` arasında gerçekleştirilmiştir. Her bir soru için dört metrik ayrı ayrı değerlendirilmiş, daha sonra model düzeyinde ortalama, standart sapma, medyan, alt-üst sınır ve %95 güven aralığı hesaplanmıştır.

## 5. Hakem Model ve Kör Değerlendirme İlkesi

Değerlendirme aşamasında üretici model ailesinden bağımsız bir hakem model kullanılmıştır. Hakem model olarak `openai/gpt-oss-120b` seçilmiş, istemlerde model adı, model ailesi veya üretim koşulunu açığa çıkarabilecek herhangi bir tanımlayıcı bilgiye yer verilmemiştir. Böylece değerlendirme sürecinde öz değerlendirme yanlılığının azaltılması hedeflenmiştir.

Hakem istemleri kısa, rubrik temelli ve tek metriğe odaklı olacak biçimde yapılandırılmıştır. Üretilecek çıktı, yalnızca sayısal skor olacak biçimde sınırlandırılmış; sıcaklık değeri `0.0` ve sabit tohum (`seed = 42`) kullanılarak tekrar üretilebilirliğin artırılması amaçlanmıştır. Ayrıca gereksiz reasoning üretiminin önüne geçebilmek için `include_reasoning = False` ve `reasoning_effort = "low"` ayarları tercih edilmiştir.

## 6. LLM-as-a-Judge İstemleri

Hakem model, her soru için dört ayrı ölçüt bakımından bağımsız olarak çalıştırılmıştır. Böylece tek bir birleşik puan yerine, soru üretiminin farklı alt boyutları ayrı ayrı gözlemlenebilmiştir. Hakem modele gönderilen istemler aşağıda verilmiştir.

### 6.1. Soru Kalitesi İçin Kullanılan Prompt

Bu istem, sorunun açıklığı, tek bir en iyi cevaba sahip olması, konu ile uyumu ve eğitimsel değeri bakımından değerlendirilmesi amacıyla kullanılmıştır:

```text
Metric: question_quality
Judge whether the item is clear, unambiguous, science-topic aligned, and has one best answer.
Rubric: 0.0 invalid or confusing, 0.5 answerable but weak, 1.0 clear and educationally strong.
Question: {question}
Topic: {topic}
```

Bu isteme karşılık hakem modelden yalnızca `0` ile `100` arasında tek bir tam sayı döndürmesi istenmiş; daha sonra bu değer `0.0–1.0` aralığına normalize edilmiştir.

### 6.2. Cevap Doğruluğu İçin Kullanılan Prompt

Bu istem, doğru cevap olarak sunulan seçeneğin soruya ve konuya göre olgusal açıdan doğru olup olmadığını ölçmek için kullanılmıştır:

```text
Metric: answer_correctness
Judge whether the proposed correct answer is factually correct for the question and topic.
Rubric: 0.0 incorrect, 0.5 partly correct, 1.0 fully correct.
Question: {question}
Answer: {answer}
Topic: {topic}
```

Bu ölçütte amaç, cevabın yalnızca konu ile ilişkili olup olmadığını değil, gerçekten doğru bilgi içerip içermediğini sınamaktır.

### 6.3. Çeldirici Kalitesi İçin Kullanılan Prompt

Bu istem, yanlış seçeneklerin alan içi, makul ve buna rağmen yanlış olup olmadığını değerlendirmek amacıyla kullanılmıştır:

```text
Metric: distractor_quality
Judge whether all distractors are plausible within the same domain yet still incorrect and non-duplicative.
Rubric: 0.0 obviously bad, 0.5 mixed quality, 1.0 all distractors are strong.
Question: {question}
Correct Answer: {correct}
Distractors: {distractors}
```

Bu metrik, deney sonuçlarında en zorlayıcı boyut olarak ortaya çıkmıştır. Bu nedenle çeldirici kalitesi puanları, sistemin yalnızca doğru cevabı üretme değil, aynı zamanda pedagojik olarak işe yarar yanlış seçenekler oluşturma başarısını da göstermektedir.

### 6.4. Cevap İlgisi İçin Kullanılan Prompt

Bu istem, doğru cevap olarak verilen ifadenin soruya ne ölçüde doğrudan yanıt verdiğini ölçmek amacıyla kullanılmıştır:

```text
Metric: answer_relevancy
Judge how directly the answer responds to the exact question being asked.
Rubric: 0.0 irrelevant, 0.5 partly relevant, 1.0 directly relevant.
Question: {question}
Answer: {answer}
```

Bu ölçüt ile özellikle doğru görünen ancak sorunun sorduğu şeyi tam karşılamayan cevapların ayırt edilmesi amaçlanmıştır.

### 6.5. Hakem Modelle Etkileşim Biçimi

Yukarıdaki metrik istemlerine ek olarak hakem modele, üretilecek çıktının yalnızca skor içermesi gerektiği ayrıca belirtilmiştir. Birincil istem yapısında modelden `0–100` aralığında tek bir tam sayı istenmiş, gerekirse ikincil istem yapısında `0.0–1.0` aralığında tek bir sayısal değer talep edilmiştir. Böylece değerlendirme çıktılarının yapılandırılmış, kısa ve karşılaştırılabilir olması sağlanmıştır.

Kör değerlendirme ilkesi gereği bu istemlerin hiçbirinde üretici model adı, model ailesi, parametre boyutu veya deney koşulunu açığa çıkarabilecek meta-veri kullanılmamıştır. Dolayısıyla elde edilen skorların, içerik kalitesine dayalı göreli puanlar olarak yorumlanması amaçlanmıştır.

## 7. Sonuçların Hesaplanma ve Raporlanma Biçimi

Her model için önce dört metriğin ortalama puanları hesaplanmıştır. Daha sonra genel skor, dört ana metriğin eşit ağırlıklı ortalaması alınarak elde edilmiştir. Böylece tek bir metriğin aşırı baskın hale gelmesi önlenmiş ve soru üretim kalitesi çok boyutlu olarak değerlendirilmiştir.

Raporlama aşamasında yalnızca aşağıdaki koşulları sağlayan sonuç dosyaları kabul edilmiştir:

- tüm modellerin aynı konu listesi ile değerlendirilmiş olması,
- tüm modellerin aynı `shared_rag_contexts.json` dosyasını kullanmış olması,
- üretim yolunun `shared_contexts+production_mcq_generator` olması,
- her metrik için `count = 100` olacak biçimde tam sonuç üretilmiş olması.

Bu doğrulamalar sağlanmadan rapor oluşturulmasına izin verilmemiştir.

## 8. Geçerlilik ve Sınırlılıklar

Bu deney düzeni, retrieval varyansını büyük ölçüde kontrol altına aldığı için model karşılaştırması açısından güçlü bir çerçeve sunmaktadır. Bununla birlikte değerlendirme süreci tek bir LLM hakem üzerinden yürütülmüştür. Dolayısıyla elde edilen puanlar, insan değerlendirici ile çapraz doğrulanmış nihai pedagojik kalite ölçümleri değil; bağımsız bir LLM hakemin tutarlı rubrik puanlamaları olarak yorumlanmalıdır.

Buna rağmen aynı judge, aynı istem yapısı, aynı bağlam dosyası ve aynı örneklem tüm modeller için sabit tutulduğu için, göreli model karşılaştırmasının metodolojik açıdan anlamlı olduğu değerlendirilmektedir.
