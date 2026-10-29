# Troubleshooting

Something doesn't work? Start here.

**Contents**

- [First: how to read an error](#first-how-to-read-an-error)
- [Startup errors](#startup-errors)
- [Google Sheets](#google-sheets)
- [Telegram errors](#telegram-errors)
- [The bot runs but doesn't react](#the-bot-runs-but-doesnt-react)
- [The bot does something unexpected](#the-bot-does-something-unexpected)
- [Windows tips](#windows-tips)
- [Known limitations](#known-limitations)

---

## First: how to read an error

- **Python errors** end with a block called a *traceback*. **Read the last line first** – it names the problem (`FileNotFoundError: …`, `KeyError: …`). The lines above it show where in the code it happened.
- **The log** is written to the terminal and to `logs/logsDD_MM_YYYY_.log` (one file per day). Every line has a level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. Search the file for `ERROR` and `CRITICAL` first.
- Useful log phrases for following a message through the bot:

  | You see… | It means… |
  |---|---|
  | `Received new message, message text: …, from <username>` | Telegram delivered the message to the restaurant's bot. **If this line is missing, the problem is on the Telegram side** (bot not in the group, privacy mode, wrong token). |
  | `Is_from_UCS -- Ben` / `-- False` | Whether the sender was recognised as a team member. |
  | `New issue report ⚠! Warning level 0` | An issue was opened. |
  | `message is discussion of problem. doing nothing` | The message matched no rule – see [How it works → the rules](how-it-works.md#3-the-life-of-an-issue). |
  | `Difference in chat_id!!!` | Harmless. It's logged for every message because `.env` stores the ID as text and Telegram sends a number. |
  | `Initialisation not yet complete. ⏰` | The bot ignores messages for a short time after starting (75 s in production). Wait. |

---

## Startup errors

| Error message | Cause and fix |
|---|---|
| `'python' is not recognized as an internal or external command` (Windows) | Python isn't on the `PATH`. Reinstall it and tick **Add Python to PATH**, or try `py` instead of `python`. |
| `ModuleNotFoundError: No module named 'telebot'` (or `gspread`, `dotenv`, `holidays`) | The packages aren't installed in the Python you're using. Activate the virtual environment (`venv\Scripts\activate` / `source venv/bin/activate`) and run `pip install -r requirements.txt`. **Don't** `pip install telebot` – that is an unrelated package. The right one, `pyTelegramBotAPI`, comes with `requirements.txt`. |
| `ModuleNotFoundError: No module named 'tkinter'` | `main.py` imports the Windows control-panel code on every system. Install tkinter: Debian/Ubuntu `sudo apt install python3-tk`; the python.org installers for Windows and macOS include it. |
| `FileNotFoundError: … 'logs/logs…log'` | The `logs` folder doesn't exist. Create it (`mkdir logs`) in the project folder. |
| `FileNotFoundError: … 'statistics/ben.txt'` (appears when the first issue is closed) | Create the `statistics` folder (`mkdir statistics`). The sheet row and the code menus already worked by then; only the text log failed. |
| `FileNotFoundError: … 'resolution_codes.json'` (or `error_codes.json`) | You started the bot from the wrong folder. `cd` into the project folder (the one containing `main.py`) first. |
| `FileNotFoundError: … 'service_account.json'` | The Google key file is missing or misnamed. See [Getting started → 5d](getting-started.md#5d-give-the-bot-access-a-service-account). |
| `AttributeError: 'NoneType' object has no attribute 'upper'` pointing to `sheets.py` | `GOOGLE_SHEETS_SPREADSHEET_NAME` isn't set, which usually means **`.env` wasn't found**. It must be called exactly `.env` (on Windows, Notepad likes to save it as `.env.txt` – check with *View → File name extensions*), and sit next to `main.py`. |
| `TypeError: list indices must be integers or slices, not NoneType` in `supporting_today` | There is no row for **today's date** in the `Support` tab, or the date isn't written like `29-Oct-2026` (no leading zero on the day). See [Getting started → 5b](getting-started.md#5b-fill-the-support-tab-who-is-on-duty). |

---

## Google Sheets

**Symptom:** the log shows `[ERROR CONNECTING WITH GSPREAD] … Retrying after 10 seconds` five times and then the program stops with `AttributeError: 'NoneType' object has no attribute 'worksheets'`.

**Cause:** the bot couldn't open the spreadsheet. The real reason is *not* printed, so find it with this one-liner (replace the name with your spreadsheet's title; run it in the project folder):

```bash
python -c "import gspread; sh = gspread.service_account('./service_account.json').open('YOUR SPREADSHEET NAME'); print([w.title for w in sh.worksheets()])"
```

| It prints… | Meaning and fix |
|---|---|
| your tab names | Google access works. Check that the three `GOOGLE_SHEETS_…` names in `.env` match exactly (capitals and spaces count). |
| `gspread.exceptions.SpreadsheetNotFound` | The name is misspelled **or the spreadsheet isn't shared** with the service account. Open `service_account.json`, copy `client_email`, and share the sheet with that address as **Editor**. |
| `APIError … 403 … Google Drive API has not been used in project … or it is disabled` (or the same for *Sheets*) | In Google Cloud Console → *APIs & Services → Library*, enable **both** the Google Sheets API and the Google Drive API for the project the service account belongs to. Wait a minute and retry. |
| `FileNotFoundError` | `service_account.json` is missing from the folder you are in. |

**Other sheet-related errors**

| Error | Cause and fix |
|---|---|
| `gspread.exceptions.WorksheetNotFound` | A tab name in `.env` doesn't match the tab in the spreadsheet. |
| `TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'` in `upload_issue_data` (when the first issue is closed) | The bot found no empty row in column A of the `SupportData` tab. On a fresh sheet put an `x` in a far-away cell such as `Q500` ([Getting started → 5c](getting-started.md#5c-prepare-the-supportdata-tab-the-ticket-log)). |
| A closed issue is missing from the sheet, or one row looks like a mix of two issues | See [Known limitations → #2](#known-limitations). |
| Changes I made in the sheet don't show up in the bot | The bot works from local copies (`*_buff.txt`) refreshed every `--wks_upd_interval` minutes (default 5). Wait, or lower the interval. |

---

## Telegram errors

These appear in the log or terminal as `telebot.apihelper.ApiTelegramException: A request to the Telegram API was unsuccessful. Error code: …`.

| Code / text | Cause and fix |
|---|---|
| `401 Unauthorized` (or `404 Not Found`) | The bot token is wrong, has a stray space, or the variable is missing from `.env`. Copy the token from @BotFather again (`/mybots` → the bot → API Token). |
| `409 Conflict: terminated by other getUpdates request` | **Another program is reading the same bot.** Find and stop the other copy of the bot (another PC, another terminal, a leftover `python.exe` – use `kill_py.bat` on Windows). Also: don't open the `…/getUpdates` web address while the bot runs. |
| `400 Bad Request: chat not found` | The chat ID in `.env` is wrong, or the bot isn't a member of that group. Re-check with the `getUpdates` method from [Getting started → 4](getting-started.md#4-create-the-telegram-groups-and-find-their-ids). |
| `403 Forbidden: bot can't initiate conversation with a user` | The engineer has never opened a private chat with the **main bot**. They must find it in Telegram and press **Start**. |
| `403 Forbidden: bot was kicked from the group chat` / `bot is not a member…` | Add the bot back to the group. |

---

## The bot runs but doesn't react

A message in a restaurant group should produce an `@ping` immediately. If nothing happens, go through this list in order:

1. **Did the bot just start?** It ignores messages for the first 5 seconds in test mode and **75 seconds in production** (log: `Initialisation not yet complete`).
2. **Does the log contain `Received new message` for your message?** If not, Telegram isn't delivering it:
   - the bot isn't in that group (add it);
   - **Group Privacy** is still on for that bot (@BotFather → `/mybots` → Bot Settings → Group Privacy → *Turn off*, then remove and re-add the bot);
   - the token in `.env` belongs to a different bot than the one in the group;
   - the restaurant isn't started: in `--test` mode only the test channel runs; in production the restaurant must be in `channel_params` in `main.py` and have its two `.env` variables.
3. **Are you testing with your own account?** If your username is in the team list the bot treats you as an *engineer*, so your message can never open an issue. Use a second account that is not in `.env`. (Log: `Is_from_UCS -- <your name>`.)
4. **Is there already an open issue in that group?** While a restaurant is `unresolved`, further messages from non-engineers are just conversation (`message is discussion of problem`). Close it with `done` / `not an issue`.
5. **Was it a "thank you"?** Messages with *thanks / danke / …* (and no greeting) never open an issue.
6. **Is it a sticker, voice message or file?** Only text, photos and videos are processed.
7. **Does the bot recognise engineers?** If your reply doesn't stop the escalation, check your username (without `@`, exact capitals) in `<NAME>_TELEGRAM_USERNAME`. The log line `Is_from_UCS -- False` means it didn't match.

---

## The bot does something unexpected

| What you see | Why, and what to do |
|---|---|
| It pings `@None`, or a bare `@` | A `<NAME>_SECOND_TELEGRAM_USERNAME` line is **missing** from `.env` (→ `@None`) or a `<NAME>_TELEGRAM_USERNAME` value is **empty** (→ `@`). Every listed employee needs all their variables; unused ones must be present but empty (`NAME=`). |
| It pings or calls the wrong person | The on-duty person is looked up only at startup ([#1 below](#known-limitations)). Restart the bot. Also check column E of today's row, the spelling against `EMPLOYEEn_NAME`, and the order of the list. |
| The escalation stops even though nobody did anything | Any message from a recognised engineer counts as "I'm on it" – including chatting in the group or writing `done` as the *first* message. |
| An issue was closed although the engineer didn't mean it | `done` is matched anywhere in the message: `not done yet` closes it. |
| `thanks, this works now` opened a new issue | The "greeting" check finds `hi` inside *this*. Known quirk. |
| `/stat` says the restaurant "was not found" and lists names | Use the names from that list exactly, in lower case (`kfc woergl`). Only restaurants that already have a ticket in the sheet are listed. |
| `/stat` ignores my date | Use `DD.MM.YYYY` with two-digit day and month (`01.05.2024`). |
| **Chat commands (`/stat`, `/pending`, `/my_id`, `/killyourself`) stopped answering** | A known problem ([#5](#known-limitations)): after certain events the main bot stops listening for commands until it is restarted. The Control Panel's **Kill** button and `kill_py.bat` still work. |
| The private code menu never arrived | Check: started with `--req_err_resol`? The engineer pressed **Start** in a private chat with the main bot? `<NAME>_TELEGRAM_ID` correct (use `/my_id`)? The issue wasn't auto-closed (those are recorded as "Bot" and no menu is sent)? It wasn't closed within 75 seconds of the bot starting? |
| The only error button is "No data found for the given parameters." | That device has no `Software` or `Hardware` section (or no entries) in `error_codes.json` / `resolution_codes.json`. |
| A new resolution I added doesn't appear in the menu | It is saved but the menu only reads the resolution file at startup. Restart the bot. New *errors* appear immediately. |
| After tapping "No, Edit 📝" the bot goes quiet | Known problem ([#6](#known-limitations)). Use **Cancel adding ❌** instead. |
| The phone doesn't ring | Was the bot started with `--telephony`? Is the phone script connected (`Connected to …`)? Is the number in `+436601234567` format? Also see the [known newline problem](running-in-production.md#known-problem-calls-may-not-start). |

---

## Windows tips

- **PowerShell won't activate the venv** ("running scripts is disabled"): use Command Prompt (`cmd`) instead.
- **`.bat` scripts start in the wrong folder or can't find Python:** they contain a hard-coded path (`C:\Users\Rkeeper\UCSNotificationCenter`) – edit the `cd` line ([Running in production](running-in-production.md#2-the-windows-scripts)).
- **Another Python program died when I ran a script:** the scripts run `taskkill /IM python.exe /F`, which stops every Python program on the PC.
- **Emojis or Cyrillic look wrong in the terminal:** the log *file* is always written in UTF-8 and is correct; open it in a UTF-8 capable editor.

---

## Known limitations

These are properties of the current code, found while writing this documentation (each one was checked by reading the code and, where possible, running it against fake data). They're not mistakes in your setup. If you plan to change the code, they are good first candidates.

| # | Limitation | What it means in practice and what to do |
|---|---|---|
| 1 | **"Who is on duty" is read once, at startup.** | A bot that runs for days keeps escalating to the person who was on duty on the day it started. **Restart the bot daily** (e.g. a Task Scheduler job at the start of the shift). |
| 2 | **Two issues closed within one sheet-refresh window can write to the same row.** | The bot picks the next empty row from its local copy of the `SupportData` tab, which is refreshed only every `--wks_upd_interval` minutes (5 by default, 10 in `run_bot.bat`). A second ticket closed before the next refresh targets the same row and **overwrites** the first. With many restaurants this can happen. Lowering the interval (e.g. `--wks_upd_interval 1`) makes it rarer but doesn't remove it. Spot-check the sheet against the main-channel summaries. |
| 3 | **`/pending` and `/killyourself` only know five people.** | They decide "is this a team member?" by checking `ALEX_`, `EGOR_`, `VOVA_`, `IVAN_` and `IGOR_TELEGRAM_USERNAME` (plus the `…_SECOND_…` of Egor and Vova), no matter who is in `EMPLOYEEn_NAME`. Other team members cannot use these commands, and `/pending` shows only tickets whose employee column is one of those five names. **If one of those variables is missing from `.env` entirely, a Telegram user without any @username is accepted as that person**, so keep the lines (empty is safe). |
| 4 | **`/pending` without arguments may use an old month.** | The "current month and year" are fixed when the bot starts. After the month changes, give it explicitly: `/pending 11 2026`. |
| 5 | **Chat commands can go silent.** | While a code menu is open the bot pauses its command listener, and a few paths forget to switch it back on: an issue **auto-closed** after 3 reminders when `--req_err_resol` is on, choosing **Not an issue** in the menu, closing an issue in the first 75 s after startup. After that `/stat`, `/pending`, `/my_id` and `/killyourself` don't answer until the bot is restarted. |
| 6 | **The "No, Edit 📝" button misbehaves.** | The edited text is saved as a new code, but then the bot waits silently; tapping **Yes 👌** again also saves the *first* text. Use **Cancel adding ❌** instead. |
| 7 | **New resolution codes appear in the menu only after a restart.** | They're saved and applied to the current ticket immediately, but the menu reads the file once at startup. |
| 8 | **Phone calls may not start.** | The server's line break makes the phone script's number check fail. Details and the likely fix: [Running in production](running-in-production.md#known-problem-calls-may-not-start). |
| 9 | **Holiday payment is written to the wrong row, or not at all.** | A background thread writes `40` into column D of the `Support` tab on Austrian public holidays. It writes one row **above** today's row (checked with simulated data), and on days 1–9 it looks for a date with a leading zero (`05-Oct-2026`) while the rest of the bot expects none, so it can fail to find the row (an error, after which that background thread ends). Check column D after each holiday. |
| 10 | **Open issues are lost on restart.** | All state is in memory. After a restart every restaurant is "resolved" again. Use `--spec_stat` when restarting while incidents may be open. |
| 11 | **Package versions are pinned on purpose.** | `requirements.txt` fixes versions such as `gspread~=5.9.0` and `pyTelegramBotAPI~=4.12.0`. Newer major versions can change function signatures (for example, `Worksheet.update` in gspread 6). Don't upgrade without testing. |
| 12 | **Needs `logs/` and `statistics/` folders, a row for today, and a spare row in the log tab.** | None are created automatically; see [Getting started](getting-started.md). |
