# סקירת PLAN-002RF WP0

התוצאה: אי־אפשר לסגור את U-8 או את WP0. נקודת הביקורת היא ה־commit הנכון, אך אינדקס הראיות אינו תקף לבייטים שב־commit, תנאי עץ עבודה נקי נכשל, ופרטי הריצה אינם מוכיחים ספק OpenAI או היעדר fallback. נוסף לכך, פרוטוקול U-8 אינו פונקציית החלטה שלמה וקוד הבדיקה אינו מממש את גבולות ה־fail-closed שהוא מתיימר לבדוק.

## 1. זהות ריצה סמכותית

המקור הוא רשומת ה־session המקומית של הריצה הנוכחית, לא ניסוח בפרומפט:

| שדה | ערך סמכותי |
|---|---|
| Provider מוגדר | `headroom` |
| Model ID מדויק | `gpt-5.6-sol` |
| Reasoning effort | `xhigh` |
| Codex CLI | `0.144.6` |
| Session/thread ID | `019ff98d-150a-7a63-a337-e2f91e712835` |
| Turn ID | `019ff98d-3147-7b93-bc04-0a53ba57eb83` |
| Fallback התרחש | **לא זמין** — אין שדה fallback ברשומת הריצה |
| ספק OpenAI first-party | **לא מוכח** — אסור להמיר את הכינוי `headroom` ל־OpenAI בהסקה |

ראיות: `rollout-2026-08-13T08-16-40-019ff98d-150a-7a63-a337-e2f91e712835.jsonl:1,8`. לכן דרישת הזהות ב־`HANDOFF-PLAN-002RF-WP0-to-review.md:39` אינה מוכחת במלואה: הדגם המדויק מאומת, אך ספק OpenAI והיעדר substitution/fallback אינם מאומתים.

## 2. נקודת הביקורת והפאקט

- `HEAD` הוא בדיוק `d9ee296058b2bb7d550f2279ca3a6801c9c4675b`.
- עץ העבודה **אינו נקי**. נמצאו:

  - `?? .hermes/tmp/wp0-openai-review-events.jsonl`
  - `?? .hermes/tmp/wp0-openai-review-stderr.log`
  - `?? .hermes/tmp/wp0-review-prompt.txt`

- אין שינויים בקבצים tracked. כל בדיקת התוכן המחויב בוצעה מול `git show d9ee296...:<path>`, ולכן הממצאים להלן קשורים ל־commit המדויק ולא לקבצי עבודה מותמרים.
- הפאקט אינו נמצא ב־commit או ב־worktree הנוכחי; הוא נמצא ב־checkout הראשי בנתיב החיצוני המתועד.
- SHA-256 של הפאקט נבדק ישירות והוא בדיוק:

`95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7`

לא הורצו בדיקות, לא נקרא/עובד קובץ הרסטר, לא הותקנו תלויות ולא נעשה שימוש במקורות רשת.

## 3. ממצאים

### CRITICAL

1. **אינדקס הראיות אינו מאמת את הבייטים שב־commit.**

`EVIDENCE-INDEX.json:11-23,46-53` מכיל גודל ו־SHA-256 של גרסאות CRLF בעץ העבודה, לא של ה־Git blobs ב־checkpoint:

| קובץ | רשום באינדקס | ב־commit |
|---|---|---|
| `cpu-feasibility-result.json` | 1780 B, `75907d5c…05d53` | 1723 B, `3a5d37ce…ad8af` |
| `cpu-feasibility-stdout.log` | 1780 B, `75907d5c…05d53` | 1723 B, `3a5d37ce…ad8af` |
| `opus-spatial-design-memo.md` | 4695 B, `96a71152…213a` | 4666 B, `96d6d73b…cad51` |
| `opus-spatial-design-metadata.json` | 694 B, `b539ac49…40b7` | 669 B, `060bf2d3…e5d8e` |

14 הרשומות האחרות תקינות וכל הקבצים שנוספו מכוסים, פרט לאינדקס עצמו. הכשל נובע מנרמול LF בזמן ה־commit, אך הסיבה אינה משנה את התוצאה: האינדקס אינו תקף ל־checkpoint. הדבר מפר את AT-23/AT-26 בפאקט, שבו hash mismatch ואינדקס לא מדויק חוסמים קבלה (`approval-packet.md:107,110`).

2. **זהות הספק והיעדר fallback של המבקר אינם מוכחים סמכותית.**

ה־session מאמת `gpt-5.6-sol`, אך מזהה את הספק כ־`headroom` ואינו מכיל שדה fallback. לכן אין אפשרות להצהיר סמכותית “OpenAI provider, no fallback”. בהתאם ל־`HANDOFF...:39`, סקירה זו אינה יכולה לשמש לבדה לסגירת שער ה־cross-provider, אף שהיא מספקת ממצאים עצמאיים.

### MAJOR

1. **פרוטוקול U-8 אינו מכסה את תוצאת הדגימה שלו.**

`opus-spatial-design-full.md:409-410` דורש לשם W-05/W-06 שני anchors ואמת עצמאית — שני דברים שהדגימה ידועה כחסרה. עם זאת:

- GO ו־PARTIAL דורשים שכל W-01…W-08 יעברו (`:433-439`);
- STOP אינו כולל כשל W-03…W-06 (`:440-441`).

לכן הדגימה הנוכחית אינה נכנסת באופן חד־משמעי לאף ענף. בפועל `cpu-feasibility-result.json:4-8` מסווג אותה כ־STOP בגלל אותם חוסרים. זו אי־התאמה לוגית בליבת ההצעה לסגירת U-8.

אותו סעיף מציע “raise the memory cap” (`:437`) ובאותו משפט אוסר החלשת שערים (`:439`). העלאת סף הזיכרון לאותה מעטפת היא החלשת gate, בניגוד לפאקט (`approval-packet.md:142`). אין לאשר אפשרות זו.

2. **הקוד מאפשר GO על manifest לא סמכותי.**

`tools/wp0_cpu_feasibility.py:55,70-78` בודק רק התאמת hash, ערך truth בוליאני/מחרוזת path ומספר anchors. הוא אינו בודק:

- `rights.status == approved` או רישיון מותר;
- שקובץ truth קיים, hash-bound ועצמאי באמת;
- תוכן, סמכות, pixel span או אי־תלות של anchors;
- גרסאות הסביבה מול `uv.lock`.

עם hash תואם, `truth.independent=true`, מחרוזת path שרירותית ושני dictionaries ריקים, הקוד מגיע ל־`GO_TO_LOCKED_CORPUS_ONLY` ב־`:100`. זה אינו fail-closed לפי W-02/W-05/W-06. הבדיקות ב־`tests/unit/test_wp0_cpu_feasibility.py:9-63` אינן מכסות מקרים אלה.

3. **בקרות המשאבים והאבטחה המתוארות בפרוטוקול אינן ממומשות.**

`tools/wp0_cpu_feasibility.py`:

- פותח ומפענח את התמונה ללא containment, reparse/junction, allow-list, header-only cap או bomb-warning enforcement (`:28-33`);
- בודק זמן רק אחרי שהפעולה הסתיימה, ללא timeout או process-tree kill (`:83-96`);
- משתמש ב־`tracemalloc`, שאינו מודד את רוב הקצאות Pillow/NumPy (`:82-96`);
- כותב לנתיב שרירותי, יוצר directories וכותב לא־אטומית (`:125-131`).

הדבר אינו עומד בבקרות `approval-packet.md:160-162`. המסמכים מודים נכון שהמספרים diagnostic-only, אך אין לראות בסקריפט הוכחת resource/security feasibility.

4. **הייצוג המכונתי מערבב diagnostic refusal עם Product-B feasibility.**

`cpu-feasibility-result.json:4-8` ו־`EVIDENCE-INDEX.json:3` אומרים רק `STOP`, בשל חוסר truth/anchors. מנגד, המזכר קובע במפורש שדיוק Product B הוא `NOT EVALUABLE` ולא GO/STOP (`opus-spatial-design-full.md:443-445`).

הפרוזה ב־ADR, ב־handoff וב־RUN-REPORT בדרך כלל מבדילה נכון: הדיאגנוסטיקה סורבה, ומשאבי/דיוק/תפוקה של Product B לא הוכחו. אבל הסכמה המכונתית אינה מבדילה בין:

- סירוב תקין של fixture לא נתמך;
- חסימת technical closure;
- מסקנה ש־Product B עצמו אינו אפשרי.

המסקנה הנתמכת היא רק: **diagnostic refusal נצפה; Product-B feasibility אינה מוכחת ואינה ניתנת להערכה מהדגימה הזאת.**

5. **אירוע `uv run` חוסם closure ואין לו שרשרת ראיות מספקת.**

`RUN-REPORT.md:67-69` ו־`dependency-license-inventory.md:17-19` מדווחים ש־`uv run` יצר `.venv` והתקין 20 חבילות ללא הרשאה. כעת:

- `.venv` אינו קיים;
- `uv.lock` הוא `a636f9bc…e0e18a`;
- `pyproject.toml` הוא `f0196ef8…02d5d`;
- אין tracked dependency change.

אבל אין באינדקס raw command log, רשימת 20 החבילות, הוכחת cache-only/offline, או ראיית מחיקה. לפיכך אפשר לאמת את מצב הסיום, לא את מלוא היסטוריית האירוע או גבול no-network. המסמכים מסווגים נכון את האירוע כחוסם AT-25; אין בסיס לעקוף אותו.

6. **Pinned-environment replay ו־TDD אינם מוכחים.**

- ה־lock דורש NumPy `2.4.6` ו־Pillow `12.3.0`.
- התוצאה נוצרה עם NumPy `2.4.3` ו־Pillow `12.2.0` (`cpu-feasibility-result.json:27-31`).
- RED היה environment-blocked, לא RED התנהגותי (`RUN-REPORT.md:30-36`).
- רק 2 בדיקות ממוקדות עברו בסביבה לא נעולה.
- full-suite collection נעצרה על תשעה import errors של `ezdxf`.
- הבדיקה ב־`test_wp0_cpu_feasibility.py:36-39` מאשרת `tracemalloc` וזמן של probe כאילו הם thresholds תקפים, אף שהמסמכים עצמם שוללים משמעות resource-feasibility למדידות אלה.

לכן AT-19, אימות TDD מלא וכל טענת resource acceptance אינם מוכחים. לא הרצתי מחדש אף בדיקה.

7. **Effort של מחבר Opus אינו מאומת, למרות ניסוח “Opus MAX”.**

`opus-spatial-design-full.md:43-54` אומר במפורש שה־MAX המבוקש אינו ניתן לאימות מתוך הסשן. גם `opus-spatial-design-metadata.json:1-24` אינו מכיל effort. לכן `HANDOFF...:15` אינו רשאי להציג “Opus MAX” כערך actual מוכח. הדגם, הספק, session ID והיעדר web-search מתועדים; effort בפועל לא.

8. **U-15 טרם נסגר.**

הפאקט עצמו נשאר חיצוני ולא tracked. ה־commit מספק digest binding, אך לא עותק Git durable של הבייטים. `numbered-decisions-u1-u15.md:23` מסווג נכון את U-15 כ־pending checkpoint; עקב אינדקס הראיות השגוי ונקודת העבודה הלא־נקייה, גם ה־checkpoint הנוכחי אינו מספיק לסגירתו.

### MINOR

1. `tools/wp0_cpu_feasibility.py:116` מחזיר תמיד הודעה שדיוק לא נמדד בגלל truth/anchors, גם אם שניהם סופקו והחוסם הוא nondeterminism או resource limit. זהו provenance לא מדויק במסלולים אחרים.

2. `cpu-feasibility-result.json:27-50` כולל platform ומשך ריצה בתוך artifact מאונדקס. אם קובץ זה נחשב “canonical evidence”, הוא מתנגש עם דרישת הפאקט להוציא duration/host metadata מראיה קנונית (`approval-packet.md:162`). סיווג הקובץ כקנוני או diagnostic אינו מפורש.

### INFO

- סטטוס ADR-0006 כ־`PROPOSED` נכון (`ADR-0006...:3`); אסור להעבירו ל־Accepted.
- U-1…U-7 ו־U-9…U-15 נשארו חסומים או מוגבלים באופן מהותי ונכון. U-8 הוא candidate בלבד.
- ה־metadata הגולמי של Anthropic עקבי לגבי `claude-opus-5`, provider `firstParty`, session `6a2a726e-170e-47fb-938f-f4dcc7f4e747`, ו־0 web-search/web-fetch.
- לא נמצאה בקוד קריאת רשת. זהו ממצא סטטי בלבד, לא הוכחת zero-socket לריצה ההיסטורית.
- אין ראיה להפעלת route, לפלט גאומטרי, ל־GPU/H200, ל־WP1 או ל־PLAN-003.

## 4. קריטריוני קבלה

### הוכחו

- HEAD המדויק.
- SHA-256 המדויק של הפאקט החיצוני.
- אין שינוי tracked בעץ העבודה.
- exit code מתועד `3`.
- שתי תוצאות probe זהות בבייטים לפי הראיה שנשמרה.
- התוצאה אינה כוללת גאומטריה או ציון accuracy/yield.
- מצב ADR נשאר Proposed והנתיבים נשארו default-off.
- 14 מתוך 18 רשומות האינדקס מאמתות את ה־Git blobs.

### לא הוכחו

- worktree נקי.
- שלמות EVIDENCE-INDEX ל־checkpoint.
- Provider OpenAI והיעדר fallback של המבקר.
- actual MAX effort של מחבר Opus.
- hash הרסטר באמצעות בדיקה עצמאית בריצה זו — נאסר עליי לעבד את fixture.
- pinned-environment determinism.
- full test suite או RED תקין.
- Product-B accuracy, yield, topology, scale או resource feasibility.
- peak working set, hard/soft RSS behavior, timeout/tree-kill או adversarial matrix.
- zero-network של הריצה ההיסטורית או של `uv run`.
- AT-25, AT-26, U-8 או U-15.
- WP0 technical closure.

## 5. ביקורת אבטחה וגבולות

- הסקירה הנוכחית לא ערכה קבצים, לא staged/committed, לא התקינה תלויות, לא הפעילה בדיקות ולא קראה את הרסטר. עם זאת, מעטפת ההרצה יצרה/מנהלת שלושה קבצי `.hermes/tmp`, ולכן תנאי read-only ברמת עץ העבודה אינו נקי.
- קריאת המודל המרוחקת של Anthropic היא planning provenance, לא Product-B execution. `web_search_requests=0` ו־`web_fetch_requests=0` אינם שקולים להוכחת zero-network של המחשב המקומי.
- אירוע ההתקנה הוא הפרת גבול מפורשת, גם אם rollback השאיר locks ללא שינוי.
- הקוד אינו אוכף path containment, format/resource limits, process isolation, network observation, atomic finalization או trusted-manifest semantics.
- לא מוצע manual fallback, OCR, הורדת thresholds או rescue path.

## 6. פסק דין

**BLOCKED**

U-8 **אינו יכול להיסגר**. WP0 **אינו יכול להשלים technical closure**; הוא נשאר בתוצאת STOP/needs-input עם Product-B feasibility בלתי מוכחת. WP1 נשאר **בלתי מורשה**, ואין להתחילו אוטומטית.