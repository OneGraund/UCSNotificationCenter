# Configuration reference

Everything you can change, and where. Use this page to **look things up**; if you're setting up for the first time, follow [Getting started](getting-started.md) first.

**Contents**

1. [Where settings live](#1-where-settings-live)
2. [`.env` variables](#2-env-variables)
3. [Command-line options](#3-command-line-options)
4. [Constants in the code](#4-constants-in-the-code)
5. [Google Sheet layout](#google-sheet-layout)
6. [Adding a restaurant](#adding-a-restaurant)
7. [Adding or changing an employee](#adding-or-changing-an-employee)
8. [Adding error and resolution codes](#adding-error-and-resolution-codes)

---

## 1. Where settings live

| What | Where | Changes take effect |
|---|---|---|
| Secrets (bot tokens), chat IDs, people, phone numbers, sheet names | `.env` | after restarting the bot |
| How the bot behaves on this run (test mode, intervals, notifications…) | command-line options when you start `main.py` | on that run |
| The list of restaurants, escalation times | top of `main.py` | after restarting the bot |
| Known errors and fixes | `error_codes.json`, `resolution_codes.json` | errors: immediately; fixes: after restart (see [below](#adding-error-and-resolution-codes)) |
| Who is on duty, ticket log | Google Sheet | ⚠️ the on-duty person is looked up **only when the bot starts**, not every day – restart the bot when the duty changes. The ticket log is read through [the sheet buffer](how-it-works.md#the-sheet-buffer-and-why-it-matters). |

---

## 2. `.env` variables

`.env` is a plain text file in the project folder, one `NAME=value` per line, no spaces around `=`, no quotes. Lines starting with `#` are comments. A ready-made template is in [`.env.example`](../.env.example). Variable names are **case-sensitive on Linux/macOS** and must be spelled exactly as below, including the odd capitalisation.

### Main bot and internal group (production)

| Variable | Meaning |
|---|---|
| `UCS_Support_Bot_TELEGRAM_API_TOKEN` | Token of the main bot, from @BotFather. |
| `UCS_AUSTRIA_CHAT_ID` | Chat ID of the internal team group where summaries are posted (a negative number such as `-1001234567890`). |

### Test mode (`--test`)

| Variable | Meaning |
|---|---|
| `TEST_UCS_SUPPORT_Bot_TELEGRAM_API_TOKEN` | Token of the *test* main bot. |
| `TEST_UCS_SUPPORT_CHAT_ID` | Chat ID of the test internal group. |
| `TEST_CHAT_ID` | Chat ID of the pretend-restaurant group. |
| `UCS_Support_Bot_TELEGRAM_API_TOKEN` | **Reused:** in test mode this token belongs to the pretend restaurant's bot. So test mode needs two different tokens in total. |

### The support team

The team is a numbered list. The bot reads `EMPLOYEE1_NAME`, `EMPLOYEE2_NAME`, … up to `EMPLOYEE19_NAME` and **stops at the first empty one**, so the list must always end with an empty entry (e.g. `EMPLOYEE6_NAME=`). Without it, the bot adds "None" employees.

**The order is the escalation order** (priority 0, 1, 2, …). At startup the person who is on duty today moves to the front; see [the escalation timeline](how-it-works.md#4-the-escalation-timeline).

For each name, these four variables must exist. Write the name in **capital letters** in the variable name; e.g. for `Alex` they are `ALEX_TELEGRAM_USERNAME` and so on:

| Variable | Meaning | May be empty? |
|---|---|---|
| `<NAME>_TELEGRAM_USERNAME` | Telegram `@username`, **without** the `@`, spelled exactly as Telegram shows it (capitals matter). | Not really: if empty, the person is never recognised and pings show a bare `@` |
| `<NAME>_SECOND_TELEGRAM_USERNAME` | Optional second account of the same person. They are pinged together and either account is recognised. | **Yes, but the line must exist** as `NAME=` |
| `<NAME>_TELEGRAM_ID` | Numeric ID of the person's private chat with the main bot (get it with `/my_id`). Needed for the code menus. | Yes if you don't use `--req_err_resol` |
| `<NAME>_MAINCELLPHONE_NUMBER` | Phone number in international format, e.g. `+436601234567`. Needed for phone calls. | Yes if you don't use calls |

Notes:

- The name in `EMPLOYEEn_NAME` is also what's written into the Google Sheet and what you put in the `Support` tab as "who is on duty". It's case-sensitive.
- **Five names are special:** `ALEX`, `EGOR`, `VOVA`, `IVAN`, `IGOR`. The commands `/pending` and `/killyourself` check "is this a team member?" against exactly these five names (`ALEX_TELEGRAM_USERNAME`, `EGOR_TELEGRAM_USERNAME`, `EGOR_SECOND_TELEGRAM_USERNAME`, `VOVA_…`, `VOVA_SECOND_…`, `IVAN_…`, `IGOR_…`). **Keep all of those lines in `.env`, even when someone isn't on your team (leave the value empty).** If such a variable is missing entirely, then a Telegram user *without any @username* is accepted as that person. Details: [Known limitations](troubleshooting.md#known-limitations).

### Google Sheets

| Variable | Meaning |
|---|---|
| `GOOGLE_SHEETS_SPREADSHEET_NAME` | Title of the spreadsheet file, as shown in Google Drive. |
| `GOOGLE_SHEETS_SUPPORT_WORKSHEET_NAME` | Name of the tab with the daily on-duty schedule. |
| `GOOGLE_SHEETS_SUPPORTDATA_WORKSHEET_NAME` | Name of the tab where finished tickets are logged. |

You also need the file `service_account.json` in the project folder; see [Getting started → 5d](getting-started.md#5d-give-the-bot-access-a-service-account).

### Restaurants (production)

One chat ID and one bot token per restaurant. The first column is the **restaurant's name as it appears in the Google Sheet and in `/stat`** – it's derived from the chat-ID variable name (see [Adding a restaurant](#adding-a-restaurant)). The last column is a country/language code that is only stored in column P of the ticket log.

| Name in sheet and `/stat` | Chat ID variable | Bot token variable | Code |
|---|---|---|---|
| `test` | `TEST_CHAT_ID` | `UCS_Support_Bot_TELEGRAM_API_TOKEN` | de |
| `kfc woergl` | `KFC_WOERGL_CHATID` | `UCS_Support_Woergl_Bot_TELEGRAM_API_TOKEN` | de |
| `kfc mil` | `KFC_MIL_CHATID` | `Ucs_Support_Mil_Bot_TELEGRAM_API_TOKEN` | de |
| `kfc kosice` | `KFC_KOSICE_CHATID` | `Ucs_Support_Kosice_Bot_TELEGRAM_API_TOKEN` | sk |
| `kfc dp` | `KFC_DP_CHAT_ID` | `Ucs_Support_Dp_Bot_TELEGRAM_API_TOKEN` | de |
| `kfc flo` | `KFC_FLO_CHAT_ID` | `Ucs_Support_Flo_Bot_TELEGRAM_API_TOKEN` | de |
| `kfc brn` | `KFC_BRN_CHAT_ID` | `UCS_Support_Brn_Bot_TELEGRAM_API_TOKEN` | de |
| `kfc borymall` | `KFC_BORYMALL_CHAT_ID` | `UCS_Support_Borymall_Bot_TELEGRAM_API_TOKEN` | sk |
| `kfc trn` | `KFC_TRN_CHAT_ID` | `UCS_Support_Trn_Bot_TELEGRAM_API_TOKEN` | sk |
| `kfc aupark` | `KFC_AUPARK_CHAT_ID` | `UCS_Support_Aupark_Bot_TELEGRAM_API_TOKEN` | sk |
| `kfc eurovea` | `KFC_EUROVEA_CHAT_ID` | `UCS_Support_Eurovea_Bot_TELEGRAM_API_TOKEN` | sk |
| `kfc nivy` | `KFC_NIVY_CHAT_ID` | `UCS_Support_Nivy_Bot_TELEGRAM_API_TOKEN` | sk |
| `kfc trn dr` | `KFC_TRN_DR_CHAT_ID` | `UCS_Support_Trn_Dr_Bot_TELEGRAM_API_TOKEN` | sk |
| `kfc scs` | `KFC_SCS_CHAT_ID` | `UCS_Support_Scs_Bot_TELEGRAM_API_TOKEN` | de |
| `kfc mhs` | `KFC_MHS_CHAT_ID` | `UCS_Support_Mhs_Bot_TELEGRAM_API_TOKEN` | de |
| `kfc par` | `KFC_PAR_CHAT_ID` | `UCS_Support_Par_Bot_TELEGRAM_API_TOKEN` | de |
| `kfc col` | `KFC_COL_CHAT_ID` | `UCS_Support_Col_Bot_TELEGRAM_API_TOKEN` | de |
| `kfc vivo` | `KFC_VIVO_CHAT_ID` | `UCS_Support_Vivo_Bot_TELEGRAM_API_TOKEN` | sk |
| `kfc relax` | `KFC_RELAX_CHAT_ID` | `UCS_Support_Relax_Bot_TELEGRAM_API_TOKEN` | sk |
| `kfc lug` | `KFC_LUG_CHAT_ID` | `UCS_Support_Lug_Bot_TELEGRAM_API_TOKEN` | de |
| `kfc pl linz` | `KFC_PL_LINZ_CHAT_ID` | `UCS_Support_Pl_Linz_Bot_TELEGRAM_API_TOKEN` | de |
| `kfc europa bb` | `KFC_EUROPA_BB_CHAT_ID` | `UCS_Support_Europa_Bb_Bot_TELEGRAM_API_TOKEN` | sk |
| `kfc zvln` | `KFC_ZVLN_CHAT_ID` | `UCS_Support_Zvln_Bot_TELEGRAM_API_TOKEN` | sk |

(The first row, `test`, is the test-mode channel and is only started with `--test`.)

---

## 3. Command-line options

You pass these after `python main.py`. All are optional. Example for a production-like run:

```bash
python main.py --disable_notifications --wks_upd_interval 10 --req_err_resol --telephony
```

| Option | Default | What it does |
|---|---|---|
| `--test` | off | **Test mode.** Starts only the pretend-restaurant channel, uses the `TEST_…` main bot and chat, and fast timings (30 s … 1 min 45 s). |
| `--disable_notifications` | off | Messages the bots send to the restaurant groups arrive silently (no sound). Pings are meant to still notify the person who is pinged. |
| `--notify_on_start` | off | When the bot starts it posts three messages to the main channel: which channels are running, who is on support today, and details of the computer it runs on. |
| `--req_err_resol` | off | After an issue is closed, ask the engineer in a private chat for the error and resolution codes. |
| `--wks_upd_interval N` | `5` | Minutes between refreshes of the local copies of the Google tabs. Lower = fresher data, more Google requests. |
| `--wks_output_upd` | – | Logs a line each time a copy is refreshed. **Currently has no effect**: this is already on by default. |
| `--fast_start` | off | Skips the pause at startup (5 s in test mode, 15 s otherwise) and the "ignore messages for a while" period of the restaurant channels. Handy while developing; in production the delay protects against replayed old messages. |
| `--telephony` | off | Also start the TCP server that sends call requests to an Android phone. See [Running in production](running-in-production.md#phone-calls-optional). |
| `--telephony_ip IP` | this PC's IPv4 address | Address the phone server listens on. Only matters with `--telephony`. |
| `--telephony_port N` | `10000` | Port the phone server listens on. Only matters with `--telephony`. |
| `--spec_stat` | off | ⚠️ **Dangerous.** On start, every restaurant channel begins as *unknown*, writes *"Resolution status unknow. Please specify current chanel status"* in its group and pings the engineer on duty – **in all 22 groups**. A team member then answers one word in each group: `resolved` or `unresolved` (`unknown` and `locked` also exist). Without this option every channel simply starts as *resolved*. Use it when restarting during the day while real incidents may be open. |

`python main.py --help` prints the same list (with the author's original descriptions).

---

## 4. Constants in the code

A few settings have no option; change them in the file and restart:

| What | Where | Current value |
|---|---|---|
| Escalation times (minutes after the first message) | `PROD_TIMINGS` in `main.py` | `[3, 5, 7, 8, 10]` |
| Escalation times in test mode | `TEST_TIMINGS` in `main.py` | `[0.5, 1, 1.25, 1.50, 1.75]` |
| Ignore messages after start (production) | `INIT_DELAY` in `main.py` | 75 seconds |
| "Is it done?" interval | `self.NOTIFY_DONE_INTERVAL_MIN` in `TelegramChanel.__init__` (`bot.py`) | 30 min (1 min in test mode) |
| Reminders before auto-close | `if self.done_reminders_sent >= 3` in `TelegramChanel.sender` (`bot.py`) | 3 |
| Words that close an issue | `is_resolution_message` in `bot.py` | `done`, `erledigt` |
| Words that dismiss an issue | `monitor_incoming` in `bot.py` | `not an issue`, `not a issue`, `lock` |
| Words recognised as thanks / greetings | `is_thank_you` in `bot.py` | see the function |
| Holiday calendar | `holidays.Austria()` in `sheets.py` | Austria |

Pick timing values that come out as **whole seconds** (0.5 min = 30 s, 1.25 min = 75 s). The bot counts whole seconds and fires a warning when the count *equals* the value, so something like 0.01 min (0.6 s) would never fire. Multiples of 0.25 are safe.

---

## Google Sheet layout

The spreadsheet has two tabs the bot uses. Their names come from `.env`.

### Support tab – who is on duty

| Column | Content | Used by the bot? |
|---|---|---|
| A | Date as text, `29-Oct-2026` – day **without** leading zero, English 3-letter month | ✅ read: finds today's row |
| B, C | anything | ❌ |
| D | Holiday payment | ✍️ written on Austrian public holidays (see [Known limitations](troubleshooting.md#known-limitations)) |
| E | Name of the engineer on duty (must equal an `EMPLOYEEn_NAME`) | ✅ read |

There **must be a row for today** at startup. Row 1 is treated like any other row, so a header is fine.

### SupportData tab – the ticket log

Row 1 is a header. Each closed issue becomes one row, **written into the first row whose column A is empty**. Keep the column order:

| Col | Header (suggested) | Example | Filled in by |
|---|---|---|---|
| A | Employee | `Ben` (or `Bot`) | bot, when the issue closes |
| B | Year | `2026` | bot |
| C | Month | `10` | bot |
| D | Day | `29` | bot |
| E | Time | `14:03:59` | bot |
| F | Response time (s) | `123` | bot |
| G | Resolution time (s) | `252` | bot |
| H | Error code | `0102` | bot, after the engineer answers the menus (empty until then; `0000` = not an issue) |
| I | Resolution code | `0102` | same |
| J | Restaurant | `kfc woergl` | bot |
| K | Warning level | `warning1` | bot – the level the escalation had reached when someone reacted |
| L | Error description | `Kiosk did not start` | bot, looked up from H |
| M | Resolution description | `Restart Kiosk application` | bot, looked up from I |
| N | Device | `Kiosk` | bot |
| O | Issue type | `Software` | bot |
| P | Country | `de` | bot |

Rules:

- Don't insert, delete or reorder columns A–P. The bot addresses them by position. Extra columns to the right are fine.
- Don't leave gaps: a blank cell in column A means "next free row".
- The one-time **`x` in a far-away cell (`Q500`)** trick from [Getting started](getting-started.md#5c-prepare-the-supportdata-tab-the-ticket-log) is needed so the bot always finds an empty row. If the table ever grows beyond row 500, move the marker further down.
- "Closed" tickets whose H and I are both empty are the ones `/pending` offers to fill in.

---

## Adding a restaurant

1. **Create a bot** for it with @BotFather (see [Getting started → 3](getting-started.md#3-create-the-telegram-bots)), turn **Group Privacy off**, and add the bot to the restaurant's Telegram group.
2. **Find the group's chat ID** ([Getting started → 4](getting-started.md#4-create-the-telegram-groups-and-find-their-ids)).
3. **Add two lines to `.env`:**

   ```text
   KFC_NEWPLACE_CHATID=-1001234567890
   UCS_Support_Newplace_Bot_TELEGRAM_API_TOKEN=123456789:AAH...
   ```

4. **Add one line to `channel_params` in `main.py`** (inside the braces, before `TestChanel`). The tuple is *(chat-ID variable, token variable, country code)*:

   ```python
   'NewPlaceChanel': ('KFC_NEWPLACE_CHATID', 'UCS_Support_Newplace_Bot_TELEGRAM_API_TOKEN', 'de'),
   ```

5. **Restart the bot.** Test with a message from a non-team account.

How the name is built: the restaurant's name in the sheet and in `/stat` is the chat-ID variable name with its **last 7 characters removed**, underscores turned into spaces, in lower case. That works perfectly for names ending in `_CHATID` (`KFC_NEWPLACE_CHATID` → `kfc newplace`). The older variables ending in `_CHAT_ID` (8 characters) leave a stray trailing space in the stored name (`kfc dp `). That's harmless because the bot strips spaces when it reads its local copy, but for new restaurants **prefer the `_CHATID` ending**.

The country code (`de`, `sk`, …) is only written to column P of the ticket log; it doesn't change the bot's language.

---

## Adding or changing an employee

1. Add them to `.env`: a new `EMPLOYEEn_NAME` line **before** the empty terminator line, plus their four `<NAME>_…` variables (table in [section 2](#the-support-team)). Then move the terminator down: if you had `EMPLOYEE6_NAME=`, the new person becomes `EMPLOYEE6_NAME=Anna` and the terminator becomes `EMPLOYEE7_NAME=`.
2. Put their name (same spelling) into column E of the `Support` tab on the days they are on duty.
3. Have them open a private chat with the main bot and press **Start**, then send `/my_id` and put the number into `<NAME>_TELEGRAM_ID`.
4. Restart the bot.

The position in the list decides when they're alerted. See [the escalation timeline](how-it-works.md#4-the-escalation-timeline).

> `/pending` and `/killyourself` only recognise the five legacy names ([see above](#the-support-team)). A new person can use the chat menus and be pinged and called as normal, but those two commands will not accept them until `is_from_ucs` in `bot.py` is changed to use the team list.

---

## Adding error and resolution codes

The two lists are plain JSON files in the project folder. Both use the same shape: **device → `Software` / `Hardware` → description → code**:

```json
{
    "Kiosk": {
        "Software": {
            "No connection to MID.": "Error 0100",
            "Kiosk did not start": "Error 0102"
        },
        "Hardware": {
            "Device off": "Error 0200"
        }
    }
}
```

(The prefix is `Error` in `error_codes.json` and mostly `Resol` or `Error` in `resolution_codes.json`; only the four digits matter. How the digits are built: [How it works → codes](how-it-works.md#6-error-codes-and-resolution-codes).)

### The easy way: from the chat

An engineer taps **Else 🤷‍♂️** in the code menu, types the description and confirms with **Yes 👌** ([Using the bot](using-the-bot.md#what-if-your-error-or-fix-isnt-in-the-list)). The bot adds the entry to the JSON file with the next free number. Two things to know:

- A new **error** shows up in everyone's menu immediately.
- A new **resolution** is saved and used for the current ticket, but only shows up in the *menu* after the next bot restart (the resolution list is read once at startup).

### The manual way: edit the JSON

- Stop the bot or restart it afterwards.
- Keep the file valid JSON: straight double quotes, commas between entries but not after the last one. Paste it into a JSON validator if unsure.
- **Adding to an existing group:** use the next free number, e.g. after `Error 0110` add `Error 0111`.
- **Adding a new device** (say `Printers`): add it to **both** files, each with both a `Software` and a `Hardware` section, and give it the next two free group numbers. Currently they run up to 14, so Software = `15xx` and Hardware = `16xx`.
- **Every `Software`/`Hardware` section needs at least one entry.** The bot works out the group number from an existing entry; on an empty section, the "add new" button crashes. Seed a new section by hand with its first entry, e.g. `"Paper jam": "Error 1500"`.
- The text of the entry is the button label, so keep it short and unique within its list.

### These files and git

`error_codes.json` and `resolution_codes.json` appear in `.gitignore`, but they were committed to the repository before that, so git **does** track them. Two consequences:

- Entries added through the chat modify these files on the machine where the bot runs, and `git status` there shows them as modified.
- If someone also changes them in the repository, `git pull` on that machine (which the update scripts do) can refuse with "local changes would be overwritten". Commit or stash the server's version first, then pull.
