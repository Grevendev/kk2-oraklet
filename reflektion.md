# **Reflektion - Oraklet (KK2)**

## Inledning
När jag började med KK2-uppgiften insåg jag snabbt att den hade potential att blir mer än bara en inlämning.
Grundkraven var tydliga: bygg ett API som tar emot ett dataset, genererar statistik och låter en LLM svara på frågor baserat på dessa siffror.

Men jag ville mer.

Jag ville använda uppgiften som en **plattform för att testa mina kunskaper**, pressa mig själv och bygga något som liknar **ett riktigt enterprise-system.**
Samtidigt ville jag vara trogen uppgiftens krav - allt som efterfrågades skulle finnas med, men jag ville bygga det på ett sätt som:
- Skulle hålla i produktion
- Var modulärt och testbart
- Var robust mot fel och drift
- Kunde växa över tid
- Reflekterande hur jag vill arbeta som utvecklare

Det här projektet blev därför både en **teknisk utmaning** och en **personlig resa.**

---

## Mina mål och min utvecklingsresa

**Jag ville bygga något större än grunduppgiften - men utan att bryta mot kraven**
Det var viktigt för mig att:
- Uppfylla alla krav i KK2
- Men samtidigt bygga en arkitektur som är **realistisk, hållbar** och **professionell**
Jag ville se hur långt jag kunde ta uppgiften utan att lämna ramen för vad som faktiskt efterfrågades.
Det här innebar att jag:
- Implementerade funktioner som **schema drift, semantic drift, column lineage, ETag‑caching, circuit breaker, retry policy, timeout‑skydd, fallback‑strategi**
- Byggde en **pipeline‑arkitektur** istället för att lägga all logik i en route
- Skapade en **DataService** som hanterar verkliga dataset, inte bara “happy path”
- Skrev en **stor testsvit** som täcker allt från Parquet‑edge‑cases till AI‑cache‑beteende

Det här var inte “gör minsta möjliga”.
Det här var **hur mycket kan jag lära mig och hur långt kan jag ta detta?**

---

## Arkitektur – djupare resonemang
**1. Pipeline‑arkitektur för AI‑kedjan**
Jag valde att dela upp AI‑kedjan i tre steg:
**PromptBuilder**
Här lärde jag mig vikten av:
- Strukturerade prompts
- Att separera data från instruktioner
- Att bygga deterministiska prompts som fungerar i tester
- Att undvika att blanda affärslogik med promptlogik

**LLMRunner**
Det här steget var en av de mest komplexa delarna:
- Jag implementerade **timeout‑skydd** för att undvika hängande anrop
- Jag lade till **retry policy** med exponential backoff + jitter
- Jag lade till **circuit breaker** för att skydda systemet
- Jag byggde en **mockbar runner** för tester

Det här gav mig en djupare förståelse för hur man bygger **resilienta system.**

**ResponseParser**
Här lärde jag mig:
- Att LLM‑svar måste valideras
- Att Pydantic är ett kraftfullt verktyg för att säkerställa struktur
- Att parsing måste vara tolerant men strikt
Pipeline‑arkitekturen gav mig:
- Tydliga kontrakt
- Testbarhet per steg
- Möjlighet att mocka LLM‑delen
- En deterministisk testmiljö

---

## 2. DataService – den mest komplexa delen av projektet
Jag trodde först att AI‑delen skulle vara svårast.
Det visade sig snabbt att **data ingestion är betydligt mer komplext.**

### Jag implementerade:
- Canonical column normalization
- Schema fingerprinting
- Semantic fingerprinting
- Column lineage
- Mixed‑type detection
- Nullability‑regler
- Memory‑gränser
- Unicode‑sanering
- Excel‑formula‑skydd
- Parquet‑schema‑validering
- Nested list‑kontroller

### Jag använde dokumentation från:
- **Pandas** (dtype‑hantering, parsing, edge cases)
- **PyArrow** (Parquet‑schema, nested types, ArrowTypeError)
- **FastAPI** (request‑hantering, streaming, middleware)
- **Pydantic** (modellering, validering)
- **Apache Parquet‑specifikationen**

Det här gav mig en djupare förståelse för hur verkliga dataset fungerar — och hur mycket som kan gå fel.

---

## 3. Schema & Semantic Drift Detection
Det här var en funktion jag lade till utöver grunduppgiften.
### Jag ville att systemet skulle:
- Upptäcka när datasetet ändras
- Skydda användaren från oväntade förändringar
- Kunna blockera eller tillåta drift beroende på policy

### Jag implementerade:
- Canonical schema fingerprint
- Semantic fingerprint per kolumn
- Column lineage

Det här gav mig en djupare förståelse för data governance, något som är centralt i verkliga system.

---

## 4. Circuit Breaker + Retry Policy
LLM‑anrop är opålitliga.
Jag ville att systemet skulle:
- Hantera fel utan att krascha
- Återhämta sig automatiskt
- Skydda sig mot kaskadfel

### Jag implementerade:
- Circuit breaker med OPEN → HALF_OPEN → CLOSED
- Retry policy med exponential backoff + jitter
- Timeout‑skydd
- Fallback‑svar

Det här gav mig en **självläkande AI‑pipeline.**

---

## 5. ETag‑caching
För att undvika onödiga LLM‑anrop implementerade jag:
- ETag per fråga
- Cache invalidation vid dataset‑ändring
- TTL‑baserad cache‑expiration

Det här gav:
- Lägre latens
- Lägre kostnad
- Mindre belastning på modellen

---

## Testning – djupare reflektion
Jag byggde en testsvit med över 70 tester som täcker:
- AI‑pipeline
- Cache‑beteende
- Circuit breaker
- Retry policy
- CSV‑validator
- Parquet‑validator
- Schema drift
- Semantic drift
- API‑endpoints
- Middleware
- Download‑flöden
- Timeout‑scenarion
- Fallback‑strategi

### Alla tester är inte gröna ännu
Det finns fortfarande:
- Parquet‑edge‑cases
- Schema‑drift‑kombinationer
- Semantiska driftfall
- Några race conditions i cache‑logiken

Det här är **ett pågående arbete**, och jag ser det som en del av min utveckling — att fortsätta förbättra, felsöka och förstå varför vissa tester fallerar.

Det är exakt så verklig backend‑utveckling fungerar.

---

## Personlig reflektion – min utveckling som utvecklare
Det här projektet har lärt mig mer än någon annan uppgift hittills.
### Arkitektur
Jag har lärt mig att tänka i lager, kontrakt och ansvar.
### Testbarhet
Jag har förstått att testbarhet inte är något man lägger på i efterhand — det måste byggas in från början.
### Typning
mypy strict har tvingat mig att tänka igenom flöden och datakontrakt på ett helt nytt sätt.
### Felhantering
Circuit breakers, retry policies och timeouts har gett mig en djupare förståelse för robusthet.
### Datahantering
Jag har lärt mig mer om Parquet, Pandas och datavalidering än jag trodde att jag skulle behöva.
### Självdisciplin
Att bygga något större än uppgiften krävde struktur, planering och uthållighet.
### Yrkesstolthet
Jag ville inte bara lämna in något som “fungerar”.
Jag ville lämna in något som **jag själv skulle vara stolt över att deploya i produktion.**

---

## Teknisk bilaga – arkitekturdiagram
### Systemöversikt
```

┌──────────────────────────────────────────────────────────────┐
│                          FastAPI App                         │
│                     (Routers, Middleware)                    │
└───────────────┬──────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────┐
│                        Data Ingestion                        │
│  CSV Validator | Parquet Validator | Schema Drift | Semantics│
└───────────────┬──────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────┐
│                         DataService                          │
│   Fingerprints | Lineage | Stats Cache | Normalization       │
└───────────────┬──────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────┐
│                        AI Pipeline                           │
│  PromptBuilder → LLMRunner → ResponseParser → Cache/ETag     │
│  Circuit Breaker | Retry Policy | Timeout | Fallback         │
└──────────────────────────────────────────────────────────────┘
```
---

## Sammanfattning
Det här projektet är mer än en inlämning — det är ett bevis på:
- Min vilja att lära mig
- Min förmåga att bygga stora system
- Min disciplin i arkitektur och testning
- Min nyfikenhet och vilja att gå längre än minimumkraven

Jag har byggt något som:
- Är robust
- Är testbart
- Är skalbart
- Är säkert
- Har tydlig arkitektur
- Har enterprise‑funktioner

Och jag är inte klar — jag kommer fortsätta förbättra testsviten, fixa röda tester och utveckla systemet vidare.

--- 