# UCS Notification Center

A set of Telegram bots that make sure **IT problems reported by restaurants get picked up fast** – and that nobody has to watch 22 chat groups all day.

Every restaurant has its own Telegram group. When restaurant staff write a message there, this program:

1. **pings** the support engineer who is on duty today,
2. **escalates** to backup engineers (more pings and phone calls) if nobody reacts,
3. **follows up** with "Is it done?" until the problem is closed,
4. **records** how long everything took in a Google Sheet, and
5. **asks the engineer** (in a private chat, with buttons) what was broken and how it was fixed, so you can build statistics later.

> **New here?** Go to **[Getting started](docs/getting-started.md)**. It takes you from nothing to a working test bot, step by step.

---

## What happens when a problem is reported

```text
 Restaurant staff                         The bot                         Support team
 ────────────────                         ───────                         ────────────
 "The kiosk won't start"  ───────────►  new issue detected
                                         @pings the engineer on duty ───► sees the ping
        ...3 minutes, nobody answers...
                                         phones the engineer on duty
        ...5 minutes...                  pings the 2nd engineer
        ...7 minutes...                  pings the 3rd, phones the 2nd
        ...8 / 10 minutes...             pings, then phones, the 4th
                                                                          someone replies  ◄── escalation stops
                                         "Is it done?" every 30 min
 "Done"                   ◄───────────  issue closed, summary posted,
                                         row added to Google Sheet
                                         asks the engineer for the
                                         error code + fix (private chat) ◄─ answers with buttons
```

The times above are the production defaults. Details are in [How it works](docs/how-it-works.md).

## What's in the box

| Feature | Short description |
|---|---|
| **Issue detection** | Any message from a non-team member in a restaurant group opens an issue. Polite "thanks" messages are ignored. |
| **Escalation** | Five warning levels over 10 minutes: Telegram pings and (optionally) real phone calls through an Android phone. |
| **Follow-up** | "Is it done?" reminders; auto-closes after 3 unanswered reminders. |
| **Google Sheets logging** | Response time, resolution time, who fixed it, which restaurant, which warning level. |
| **Error/resolution codes** | Guided button menus: device → software/hardware → error → fix. Staff can add new codes from the chat. |
| **Statistics** | `/stat <restaurant> from DD.MM.YYYY till DD.MM.YYYY` shows how often each error happened. |
| **Control panel** (Windows) | Small window with **Kill** and **Update** buttons; plus a `/killyourself` chat command. |

## Quick start (about 30–60 minutes the first time)

You need **Python 3.10 or newer**, **Git**, a **Telegram** account and a **Google** account.

```bash
git clone https://github.com/OneGraund/UCSNotificationCenter.git
cd UCSNotificationCenter
python -m venv venv                  # create an isolated Python environment
# Windows:      venv\Scripts\activate
# macOS/Linux:  source venv/bin/activate
pip install -r requirements.txt
mkdir logs                           # two folders the bot writes to (not in git!)
mkdir statistics
cp .env.example .env                 # then fill in .env  (Windows: copy .env.example .env)
```

Then create your Telegram bots and Google Sheet, fill in `.env`, and start the bot in **test mode**:

```bash
python main.py --test --notify_on_start
```

The full walk-through, including how to create the bots and the sheet, is in **[Getting started](docs/getting-started.md)**.

> ⚠️ Always start the bot **from the project folder** (the one containing `main.py`). It looks for `.env`, `service_account.json` and the code lists using relative paths.

## Documentation

| Read this... | ...if you want to |
|---|---|
| **[Getting started](docs/getting-started.md)** | Install everything and run your first test |
| **[How it works](docs/how-it-works.md)** | Understand the concepts, the issue life-cycle, the escalation timeline and the code layout |
| **[Using the bot](docs/using-the-bot.md)** | Know what to type in Telegram: commands, closing issues, filling in codes *(for support engineers)* |
| **[Configuration reference](docs/configuration.md)** | Look up every `.env` variable, command-line option and Google Sheet column; add restaurants, employees or codes |
| **[Running in production](docs/running-in-production.md)** | Run it 24/7 on Windows, update it, set up phone calls |
| **[Troubleshooting](docs/troubleshooting.md)** | Fix an error message, or check the known limitations |

## Project layout

```text
UCSNotificationCenter/
├── main.py                  ← START HERE: reads options, builds everything, launches the bots
├── bot.py                   ← the brain: issue tracking, escalation, private-chat menus, chat commands
├── sheets.py                ← everything that talks to Google Sheets
├── statistics.py            ← error/resolution code lists, /stat maths and formatting
├── sip_call.py              ← phone-call requests + the small TCP server for the Android phone
├── cellphone_clientcaller.py← script that runs ON the Android phone and places the calls
├── gui.py                   ← the Windows "Control Panel" window (Kill / Update)
├── utils.py                 ← date helpers and the Logger
├── error_codes.json         ← list of known errors, grouped by device and software/hardware
├── resolution_codes.json    ← list of known fixes, same structure
├── requirements.txt         ← Python packages to install
├── .env.example             ← template for your secret settings (copy to .env)
└── windows_console_managment/  ← .bat scripts to start / update / kill the bot on Windows
```

Files you create yourself and that are **never committed to git**: `.env`, `service_account.json`, `logs/`, `statistics/`.

## Security in one paragraph

`.env` (bot tokens, phone numbers) and `service_account.json` (Google access) are secrets. They are listed in `.gitignore`; keep it that way and never paste them into chats, issues or screenshots. If a bot token leaks, revoke it in Telegram's @BotFather (`/revoke`) and put the new one in `.env`.

## Good to know

This is an internal tool that grew with one team's setup, so some things are hard-coded (the list of restaurants lives in `main.py`; two chat commands recognise a fixed list of five names). That is normal – just read [Troubleshooting → Known limitations](docs/troubleshooting.md#known-limitations) before you rely on something unusual.
