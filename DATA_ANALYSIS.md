# Phân tích dữ liệu — Day 10 Data Pipeline & Observability

Tài liệu này mô tả **tính chất dữ liệu**, **những gì phát hiện được** từ dữ liệu thật đã thu thập, và **luồng xử lý dữ liệu** của pipeline RAG dùng nguồn Crossref.

> Mọi con số trong tài liệu được trích xuất từ artifact thực tế trong `data/` (lần chạy gần nhất, `run_date` = ngày chạy). Pipeline có thể re-run để cập nhật.

---

## 1. Tổng quan nguồn dữ liệu

| Hạng mục | Giá trị |
|---|---|
| Nguồn | Crossref REST API — endpoint `https://api.crossref.org/works` |
| Loại dữ liệu | Metadata của công bố học thuật có DOI (tiêu đề, abstract, tác giả, ngày, URL…) |
| Query | `"agentic retrieval augmented generation large language model"` |
| Filter | `from-pub-date:<180 ngày gần nhất>,has-abstract:true` |
| Số lượng yêu cầu | `rows = 24` |
| Tổng kết quả khớp trong Crossref | **100.916** bài (`total-results`) |
| Số bản ghi thực lấy về | **24** bản ghi |
| Ngưỡng freshness | 180 ngày (`freshness_threshold_days`) |

Dữ liệu là **metadata công khai, có DOI**, miễn phí, không cần API key. Crossref khuyến nghị gửi `User-Agent` kèm `mailto` để vào "polite pool" (ưu tiên rate-limit tốt hơn).

---

## 2. Tính chất dữ liệu (Data characteristics)

### 2.1. Về nguồn và phân bố loại tài liệu

Từ 24 bản ghi đã lấy:

| `type` Crossref | Số lượng | Ý nghĩa |
|---|---|---|
| `journal-article` | 15 | Bài tạp chí khoa học |
| `posted-content` | 8 | Preprint / posting (Research Square, SSRN, JMIR Preprints…) |
| `report` | 1 | Báo cáo kỹ thuật |

→ Tập dữ liệu thiên về **preprint + bài báo mới** trong lĩnh vực RAG/Agentic AI/LLM (phù hợp với chủ đề query và filter ngày).

### 2.2. Schema bản ghi thô — `PaperRecord`

Phân tích về dạng phẳng có **11 trường** (lưu tại `data/raw/crossref_records.json`):

```
paper_id          -> DOI (khóa chính, duy nhất)
title             -> tiêu đề (Crossref lưu dạng list, lấy phần tử đầu)
summary           -> abstract nguyên bản (còn thẻ <jats:...>)
authors           -> list tác giả "Given Family"
categories        -> list subject Crossref (thường rỗng)
primary_category  -> subject đầu tiên (nếu có)
published         -> ngày xuất bản, định dạng YYYY-MM-DD
updated           -> ngày cập nhật/deposited gần nhất
abs_url           -> URL DOI (trang landing)
pdf_url           -> link full-text PDF (nếu có)
comment           -> tên tạp chí/nhà xuất bản
```

> Crossref lưu dữ liệu **lồng nhau (nested)**: `title`/`container-title` là list, `author` là list of dict (`given`/`family`/`ORCID`), ngày nằm trong `{"date-parts": [[Y, M, D]]}` (thiếu tháng/ngày rất phổ biến). Pipeline phải "làm phẳng" các cấu trúc này.

### 2.3. Đặc điểm văn bản

| Trường đo | Kết quả đo được |
|---|---|
| Độ dài `summary` | **826 → 2.610 ký tự** (median **1.661**) |
| Số tác giả / bài | **1 → 7** (median **2**) |
| Bài có `pdf_url` | **24/24** (sau khi fallback về `resource`) |
| Bài có `subject` (categories) | **0/24** ← quan trọng, xem §3 |
| Bài có abstract | **24/24** (nhờ filter `has-abstract:true`) |

### 2.4. Đặc điểm thời gian (Freshness)

| Trường đo | Kết quả |
|---|---|
| Khoảng `published` | **2026-02-12 → 2026-08-01** |
| Phân bố năm | **100% năm 2026** |
| `age_days` (so với run_date) | min **5**, median **66**, max **175** |
| Trạng thái freshness | **Tất cả đều tươi** (`age_days < 180`) |

→ Bộ dữ liệu này **rất mới**, không có bản ghi stale — điều này quan trọng cho bài lab vì phần **corruption flow** sẽ phải **giả lập** dữ liệu cũ để đo tác động lên agent.

### 2.5. Đa dạng ngôn ngữ / ký tự

3/24 tiêu đề chứa ký tự ngoài ASCII:

- Dấu nháy cong `'` (U+2019) thay vì `'` (ASCII).
- Gạch nối Unicode `‐` (U+2010) thay vì `-`.
- Một tiêu đề **tiếng Nga (Cyrillic)**: *"Снижение рисков применения LLM … в сфере экономической безопасности"*.

→ Dữ liệu thật **không thuần nhất encoding/ngôn ngữ**. Ảnh hưởng trực tiếp đến việc thiết kế câu hỏi đánh giá (xem §3).

---

## 3. Những gì phát hiện được từ dữ liệu (Findings)

### 3.1. Categories bị thiếu hoàn toàn — phát hiện quan trọng nhất

**0/24 bài có trường `subject`** của Crossref. Đây là đặc trưng của preprint CS/AI: tác giả thường không gán subject theo phân loại Crossref.

**Hệ quả cho pipeline:**
- Không thể sinh câu hỏi loại `categories` có ground-truth thật (sẽ rỗng).
- Bộ test set hiện tại tự động **fallback** sang các loại câu hỏi khác (`authors`/`summary`/`date`).
- Nếu bài lab muốn kiểm tra kỹ năng "categories" của agent, cần **bổ sung nguồn category khác** (ví dụ gán từ `container-title`/tên tạp chí, hoặc từ model phân loại chủ đề) — chứ không nên bịa category.

### 3.2. Abstract chứa markup JATS/XML

Mọi abstract nguyên bản bọc trong thẻ `<jats:p>…</jats:p>`, có kèm `<jats:title>`, `<b>`, `<italic>`…
→ Bắt buộc **strip thẻ + unescape HTML entity** trước khi embed, nếu không embedding sẽ bị nhiễu bởi tag. Pipeline làm việc này ở giai đoạn cleaning, sau kiểm tra **không còn thẻ nào** sót lại.

### 3.3. Ngày xuất bản thường thiếu tháng/ngày

Crossref hay chỉ lưu `date-parts: [[2026]]` (chỉ năm). Nếu parse cứng sẽ lỗi.
→ Pipeline **pad về `YYYY-01-01`** khi thiếu. Đây là **lựa chọn an toàn**, nhưng làm giảm độ chính xác của `age_days` (có thể chênh vài chục ngày). Đây là một điểm cần ghi nhận khi diễn giải freshness report.

### 3.4. Dữ liệu sạch, không trùng lặp

- **0 DOI trùng** ở tầng raw.
- **0 paper_id trùng**, **0 title trùng** sau cleaning.
- **Tất cả summary ≥ 826 ký tự** (xa ngưỡng rác 100 ký tự).

→ Với query/filter hiện tại, **không có dữ liệu rác hay duplicate nào bị drop** ở lần chạy này. Phần corruption phải **chủ động tạo** duplicate/noise/stale để có dữ liệu lỗi đo tác động.

### 3.5. Định dạng & ngôn ngữ không đồng nhất

Như đã nêu §2.5, dấu nháy cong `'` trong tiêu đề **vượt qua filter ASCII `'`** và **không phá vỡ** regex `'([^']+)'` của tầng QA (vì regex chỉ khớp ASCII `'`). Nhưng điều này **mong manh**: nếu tiêu đề chứa dấu `'` ASCII thật, công cụ `lookup_paper` sẽ trỏ sai tài liệu → retrieval sai. Đây là lý do bước tạo test set **lọc bỏ** các tiêu đề chứa `'` ASCII.

### 3.6. Mật độ thông tin tốt cho RAG

Abstract dài (median 1.661 ký tự), giàu nội dung kỹ thuật → `text_for_embedding` (`Title | Authors | Summary`) có đủ ngữ nghĩa để embedding `all-MiniLM-L6-v2` phân biệt tốt giữa các bài. Đây là nền tảng để baseline retrieval có `retrieval_hit_rate` cao.

### 3.7. Khối lượng artifact sinh ra

| Artifact | Kích thước | Vai trò |
|---|---|---|
| `data/raw/crossref_response.json` | ~245 KB | Response HTTP nguyên bản — **audit nguồn** |
| `data/raw/crossref_records.json` | ~63 KB | Bản ghi phẳng, parse xong |
| `data/clean/papers_clean.csv` | ~100 KB | Bảng sạch (cho người/xử lý) |
| `data/clean/papers_clean.json` | ~115 KB | Bảng sạch, giữ list field (cho index) |
| `data/eval/test_set.json` | ~5 KB | 10 câu hỏi đánh giá cố định |

---

## 4. Luồng xử lý dữ liệu (Data processing flow)

```text
Crossref API (/works)
      │
      │  ① INGESTION  (src/ingestion/crossref.py)
      │     - build params từ settings (query/filter/rows)
      │     - GET với retry + exponential backoff cho 429/500/502/503/504
      │       (honor Retry-After header + jitter)
      ▼
[ crossref_response.json ]  ← raw HTTP nguyên bản (audit)
      │
      │  ② PARSE  (parse_crossref_payload)
      │     - làm phẳng nested fields (title list, author dict, date-parts)
      │     - LỌC: chỉ giữ bản ghi có đủ title + abstract
      ▼
[ crossref_records.json ]   ← list PaperRecord phẳng (11 trường)
      │
      │  ③ CLEANING  (src/ingestion/cleaning.py / build_clean_dataframe)
      │     - strip thẻ XML/JATS + unescape entity
      │     - join authors/categories -> authors_joined / categories_joined
      │     - parse published -> YYYY-MM-DD, tính age_days
      │     - tạo text_for_embedding = "Title: … | Authors: … | Summary: …"
      │     - DROP: thiếu title | summary < 100 ký tự | trùng paper_id/title
      │     - SORT: mới nhất trước
      ▼
[ papers_clean.csv ]  [ papers_clean.json ]   ← 24 dòng × 16 cột
      │
      │  ④ TESTSET  (src/evaluation/testset.py / build_test_set)
      │     - chọn các bài tươi nhất, tiêu đề "an toàn" để trích dẫn
      │     - sinh 10 câu hỏi dạng authors / summary / date / categories
      │       (mỗi câu có ground_truth + ground_truth_doc_ids)
      ▼
[ test_set.json ]           ← frozen evaluation set (10 câu)
      │
      ▼
(Phase tiếp theo: embedding + ChromaDB -> RAG agent -> đánh giá -> quality/freshness report)
```

### 4.1. Chi tiết từng giai đoạn (kèm ví dụ thực tế)

> Ví dụ dưới đây trích từ artifact thật (`data/raw`, `data/clean`, `data/eval`), dùng bài `10.47576/2949-1894.2026.7.7.023` làm mẫu "đi trọn vòng" cho parse + clean vì nó hội tụ mọi khó: markup JATS, ký tự Cyrillic, author lồng dict, thiếu subject, date-parts.

**① Ingestion — `fetch_source_records`**
- Dùng `requests.Session` với `User-Agent` lịch sự (+ `mailto` nếu có `CROSSREF_MAILTO`).
- `_get_with_retry`: thử lại tối đa **4 lần**, backoff `1.5 × 2^attempt + jitter`; **đọc `Retry-After`** khi Crossref trả 429.
- Status **không retryable** → raise ngay; status **retryable** (429/5xx) hoặc lỗi kết nối → backoff rồi thử lại.

*Ví dụ request + kịch bản retry:*
```http
GET https://api.crossref.org/works
    ?query=agentic retrieval augmented generation large language model
    &filter=from-pub-date:2026-02-09,has-abstract:true
    &rows=24
Header: User-Agent: Day10DataObservabilityLab/0.1 (mailto:...)
→ 200 OK · message.total-results = 100916 · message.items = [24 phần tử]
→ lưu nguyên bản body vào data/raw/crossref_response.json

Khi gặp lỗi tạm thời (mô phỏng):
  attempt 1: 429 Too Many Requests, Retry-After: 5   → sleep ~5s + jitter
  attempt 2: 503 Service Unavailable                 → sleep ~3s + jitter
  attempt 3: 200 OK ✅  → parse tiếp
```

**② Parse — `parse_crossref_payload`**
- Làm phẳng `message.items` → `PaperRecord`.
- **Bộ lọc ingestion**: bỏ bản ghi thiếu DOI, thiếu title, hoặc thiếu abstract/description.
- Ngày lấy theo thứ tự ưu tiên: `published` → `published-online` → `published-print` → `issued` → `posted`.

*Ví dụ "nested → phẳng":*
```text
RAW item (lồng nhau):
  DOI:       10.47576/2949-1894.2026.7.7.023
  title:     ["Снижение рисков применения LLM ..."]            ← list, lấy [0]
  author:    [{"given":"И.В.","family":"Ермаков", ...}, ...]   ← list of dict
  subject:   None                                              ← không có category
  published: {"date-parts": [[2026, 6, 15]]}                   ← nested list
  abstract:  "<jats:p>В статье проведено ..."                  ← còn thẻ JATS

  ⇓  parse_crossref_payload

PaperRecord (phẳng):
  paper_id:        "10.47576/2949-1894.2026.7.7.023"
  title:           "Снижение рисков применения LLM ..."
  authors:         ["И.В. Ермаков", "В.В. Филатов"]     ← ghép given + family
  categories:      []                                    ← rỗng vì subject=None
  published:       "2026-06-15"                          ← dàn từ date-parts
  summary:         "<jats:p>В статье проведено ..."     ← VẪN còn thẻ (giai đoạn clean mới strip)
```

**③ Cleaning — `build_clean_dataframe`**
- Regex `<[^>]+>` + `html.unescape()` để sạch text.
- Tính `age_days = run_date - published` (chuyển `run_date` về naive để tránh lỗi timezone).
- **Bộ lọc cleaning**: drop title rỗng, summary rỗng, `summary_chars < 100`, trùng `paper_id`, trùng `title`.

*Ví dụ "thô → sạch":*
```text
Đầu vào (PaperRecord):
  summary = "<jats:p>В статье проведено исследование особенностей снижения рисков..."

Đầu ra (một dòng clean):
  title:              "Снижение рисков применения LLM ..."        ← không còn thẻ
  summary:            "В статье проведено исследование ..."        ← đã strip <jats:p>
  authors_joined:     "И.В. Ермаков, В.В. Филатов"                 ← join list bằng ", "
  categories_joined:  ""                                            ← rỗng → không sinh câu hỏi categories
  published:          "2026-06-15"
  age_days:           52                                            ← run_date - published
  summary_chars:      1597                                           ← > 100 → GIỮ LẠI (không bị drop)
  text_for_embedding: "Title: Снижение рисков применения LLM ... |
                       Authors: И.В. Ермаков, В.В. Филатов |
                       Summary: В статье проведено исследование ..."
```

**④ Testset — `build_test_set`**
- Chọn bài có `authors_joined` + `summary` + tiêu đề không chứa `'` ASCII / newline.
- Câu hỏi bọc tiêu đề trong **dấu nháy đơn** `'...'` để công cụ `lookup_paper` khớp chính xác → đảm bảo `retrieval_hit` ở baseline.
- Phrasing câu hỏi căn chỉnh với bộ trích câu trả lời trong `retrieval/qa.py` (`"Who authored"` → tác giả; `"When was … published"` → ngày; `"What categories"` → chủ đề; còn lại → câu đầu summary).

*Ví dụ 3 mẫu câu hỏi (mỗi loại 1 câu) — trích từ `test_set.json`:*
```json
{ "id": "q1", "question_type": "authors",
  "question": "Who authored the paper 'SafeRAG: A Large-Language-Model-Based Multistage Retrieval-Augmented Framework for Oil and Gas Safety Report Generation'?",
  "ground_truth": "Qianwen Cao, Chiyu Zhang, Junxiong Ning, Gongru Li",
  "ground_truth_doc_ids": ["10.2118/234689-pa"] }

{ "id": "q3", "question_type": "date",
  "question": "When was the paper 'Retrieval-Augmented Large-Language-Model-Based Time-Series Forecasting for Cross-Market Equity Analysis' published?",
  "ground_truth": "2026-07-10",
  "ground_truth_doc_ids": ["10.21203/rs.3.rs-10178277/v1"] }

{ "id": "q2", "question_type": "summary",
  "question": "What is the main contribution described in the paper 'JADE-Plus: A Multimodal Agentic Retrieval-Augmented Generation ...'?",
  "ground_truth": "Abstract Diagnosing jawbone lesions in oral and maxillofacial radiology remains challenging ...",
  "ground_truth_doc_ids": ["10.1007/s10278-026-02086-9"] }
```
*Tại sao bọc tiêu đề trong `'...'`:* tầng `retrieval/qa.py` có regex `'([^']+)'` để lấy đúng tiêu đề, rồi gọi `lookup_paper` khớp exact → tài liệu đúng luôn nằm top → `retrieval_hit = True` ở baseline. Khi corruption **truncate/sửa tiêu đề**, exact-match sẽ gãy → `retrieval_hit` rớt — đây chính là cơ chế đo tác động dữ liệu lỗi.

---

## 5. Tóm tắt nhận định cho RAG

| Nhận định | Hệ quả |
|---|---|
| Dữ liệu **mới, giàu abstract, không trùng** | Baseline retrieval có tiềm năng hit-rate cao |
| **Không có categories** | Không đánh giá được kỹ năng "categories" nếu không bổ sung nguồn |
| Abstract **chứa JATS markup** | Phải strip trước khi embed |
| Ngày **thường chỉ có năm** | `age_days` có thể chênh ±vài tuần — cần ghi chú trong freshness report |
| Ngôn ngữ/encoding **không đồng nhất** | Test set phải lọc tiêu đề chứa `'` ASCII để tránh lookup sai |
| Dữ liệu sạch sẵn | Corruption flow phải **giả lập** lỗi (drop record, blank summary, noise, stale date, duplicate) để có gì so sánh |

---
*Lưu ý: các con số phản ánh lần chạy hiện tại. Khi re-run pipeline với `REFRESH_SOURCE=1`, kết quả từ Crossref có thể khác (bài mới được đăng), nhưng tính chất tổng quan (thiếu categories, markup JATS, thiên preprint) sẽ không đổi.*
