# Writing a Forix user guide

Source: the VNPM Dashboard and Clients Dashboard guides (Oct 2026) and the user's corrections on them.

## Non-negotiables (from the user's own corrections)

| Rule | User's words |
|---|---|
| English, even when the chat is Vietnamese | "bạn đổi lại viết bằng tiếng anh giúp tôi" |
| User language, zero technical terms (no API, DB, endpoint, cron, JWT, component, sync job names) | "văn phong phải dễ hiểu đúng với user guide, không kèm theo technical language" |
| One section per screen / slot / card, each with its rules + what every button does | "viết theo từng slot ... rules của slot đó, các action button trên UI để làm gì" |
| A4 landscape, text left, screenshot right | "page A4 và landscape (... text bên trái ảnh bên phải)" |
| Red boxes + numbers on what matters | "highligh những chỗ cần chú ý bằng (khung đỏ)" |
| Deliver as .docx that imports into Google Docs | "một bản như vậy mà có thể export ra google docs" |
| Nothing may spill onto the next page | "bị cut qua trang nè bạn" |
| Cut what the user says to cut, no argument | "Bỏ phần Telegram nha bạn" |
| Montserrat for the whole document | "dùng font Montserrat nữa" → "Toàn bộ tài liệu" |
| Titles are real headings (Navigation pane / Google Docs outline) | "Đánh heading á bạn" |

If the guide quotes UI text that is not English, point it out: the user fixed those strings in the app ("đổi 2 câu này luôn").

## Voice

- Second person, present tense, short sentences. "Click **Refresh**." not "The user may click the Refresh button".
- Bold exactly what the reader sees on screen: button labels, badge text, tab names. Nothing else.
- Say the real behaviour, not the placeholder: if the search box says "contact" but matches USPM names, write what it matches.
- Numbers are concrete: "30 per page", "every hour", "11:00 PM New York time", "48 hours before it expires".
- Permissions in one grey `note()` at the end of the block: "Add Rule needs the quoting rules permission (Administrator by default)."
- No marketing, no "simply", no "easily". No history ("we used to...").
- Unknown or undefined values: say so plainly ("shows Pending Definition: not defined yet").

## Page recipe

Every page is `g.page(EYEBROW, Title, left, right)`:

- **Left (40%)**: 1-2 sentence `p()` saying what the page is for, then `label()` blocks. Typical labels:
  WHEN A TICKET APPEARS / HOW TO USE (numbered steps) / READ THE BADGES (data_table) / WHEN IT LEAVES / GOOD TO KNOW. End with a grey `note()` for permissions and refresh times.
- **Right (60%)**: `g.image('NN_name.png')` then one `cap(n, ...)` per red marker, in marker order. A caption starts with the bold UI label, then what it does.
- Eyebrows group pages: BASICS, PAGES, SLOT 1 OF 7, CLIENT PROFILE · 2 OF 6, BILLING, SETTINGS, REFERENCE.
- Text-only pages (roles, FAQ) use `lw=7371, rw=7938`.

## Document recipe

1. **Cover (page 1)**: product eyebrow + big "<Product> / User Guide"; left: one-line purpose, `callout()` with the single most important rule (who can change what), IN THIS GUIDE table from `g.toc_rows()`; right: where the data comes from (source / feeds / refresh table) + "N things that hold everywhere" numbered list.
2. **Basics**: how to get in (hub URL, sign-in, error screens), navigation (top menu, sidebar, bell), buttons shared everywhere.
3. **One page per screen/section**, in the order a user meets them.
4. **Reference**: roles & permissions matrix (Admin / PM / Dev, Yes / —), "if a number looks wrong" steps, FAQ (8-10 Q&A, two columns, real questions a PM would ask).

## Length budget per page (A4 landscape, Arial 10pt)

About 170-220 words on the left, image ≤ 3.5M EMU tall plus ≤ 7 captions on the right. Over that it spills. When a page spills: shorten text first, then move a note to the other column, then shrink the image (`max_cx=4200000`). Never let a page run to two pages; split it into two titled pages instead and add both to `plan()`.

A **blank page** after a full page means an invisible empty paragraph spilled over. Same fix: trim that page.
The cover holds at most ~16 TOC rows next to the default intro.
