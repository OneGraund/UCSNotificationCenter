# Using the bot

This page is for the people who *use* the bot day to day: restaurant staff and support engineers. You don't need to install anything or know any programming.

**Contents**

1. [For restaurant staff](#for-restaurant-staff)
2. [For support engineers](#for-support-engineers)
   - [When an alert comes in](#when-an-alert-comes-in)
   - [Closing an issue](#closing-an-issue)
   - [After you close an issue: the code menus](#after-you-close-an-issue-the-code-menus)
3. [Chat commands](#chat-commands)
4. [Cheat sheet](#cheat-sheet)

---

## For restaurant staff

**Just write in your restaurant's Telegram group, like you always did.** There is nothing to learn.

When you report a problem, the bot immediately notifies the support engineer on duty by writing their `@name` in the group. If nobody reacts within a few minutes, it notifies more people and phones them. As soon as an engineer writes anything in the group, the alarms stop.

Good to know:

- Writing a short **"thanks"** or **"danke"** after the problem is solved will *not* start a new alarm.
- Photos and videos count as messages, so you can send a picture of the error. A photo's caption is read as its text. (Stickers, voice messages and file attachments are ignored.)
- Messages written by the support engineers themselves never start an alarm.

---

## For support engineers

### When an alert comes in

You're alerted by an `@yourname` ping in the restaurant's group (and, if the phone setup is running, a phone call after 3 minutes).

**To take the issue, reply in that group with any message** – for example `on it`. This is your *acknowledgement*. It stops the escalation (so your colleagues won't be pinged or called) and the main channel is told that you are working on it.

> ☝️ The bot only recognises you by your Telegram **@username** exactly as it is stored in its configuration. If it ignores you, ask the person who runs the bot to check your name in `.env`.

### Closing an issue

When the problem is fixed, write **`done`** (or German **`erledigt`**) in the restaurant group.

- If this is your **first** message since the alert, the bot treats it only as an acknowledgement. **Write `done` a second time** to actually close the issue.
- The bot looks for the letters *d-o-n-e* **anywhere** in your message. So `not done yet`, `almost done` and `abandoned` all close the issue! While an issue is open, avoid that word in other sentences.
- If you stay silent after acknowledging, the bot asks **"Is it done?"** and pings you – after 30 minutes without any message in the group, up to three times. After the third unanswered reminder it closes the issue on its own, recorded as fixed by "Bot".

**If it was a false alarm** – nobody actually needed help – write exactly one of these (as the whole message): `not an issue`, `not a issue` or `lock`. The bot answers *"Okay, issue removed"*, stops all alarms, and **no row is written** to the Google Sheet.

### After you close an issue: the code menus

If the bot was started with `--req_err_resol` (normal in production), it now sends **you a private message** with button menus. This is how the statistics get their data. It only takes a few taps.

> **First-time setup per person:** open a private chat with the **main bot** and press **Start**. Telegram does not allow bots to message people who haven't done that. Your numeric ID (`/my_id`) also has to be in the bot's configuration – ask whoever runs the bot.

The questions come one after another. Use the **buttons**:

| Step | Question | Buttons |
|---|---|---|
| 1 | *Choose device type which you fixed in …* | Kiosk · Kassa · GuestScreen · KDS · QMS · SERVER · Phones · **Not an issue** |
| 2 | *Did you have a Software-related issue or Hardware-related issue?* | Back 🔙 · Software · Hardware |
| 3 | *Choose the type of error you had* | Back 🔙 · the known errors for that device · Else 🤷‍♂️ |
| 4 | *Now specify how did you fix this issue* | Back 🔙 · the known fixes for that device · Else 🤷‍♂️ |

Then the bot says it's updating the worksheet, tells the main channel *"Got update on issue in … Error code …, resolution code …"* and fills in the error and resolution columns of your ticket's row in the sheet.

Tips:

- **Not an issue** (step 1) records the ticket with code `0000` – "Not an issue" – and skips the rest.
- **Back 🔙** goes one step back, in case you tapped the wrong thing.
- **Use the buttons, don't type.** At steps 3 and 4 any text that isn't exactly one of the buttons is treated as **Else** and starts the "add a new entry" flow below.
- **While a menu is open, the bot's chat commands (`/stat`, `/pending`, …) are paused.** Finish the menu first.

#### What if your error or fix isn't in the list?

Tap **Else 🤷‍♂️**. The bot asks you to type a short description, then shows it back to you with three buttons:

| Button | What happens |
|---|---|
| **Yes 👌** | The new entry is saved in the list (the bot picks the next free number) and used for this ticket. It's available to everyone from now on. |
| **Cancel adding ❌** | Nothing is saved; you're asked the question again. **Use this if you made a typo.** |
| **No, Edit 📝** | Meant to let you retype the text, but at the moment it misbehaves: the retyped text *is* saved, then the bot waits without asking the next question, and tapping **Yes 👌** again saves your *first* text as an additional entry. **Avoid it – use Cancel and start over.** |

Write descriptions so a colleague can understand them in a year: "Receipt printer out of paper" rather than "printer thing".

---

## Chat commands

Send commands to the **main bot** (the one that posts in your internal team group). A private chat with it is best.

| Command | Who may use it | What it does |
|---|---|---|
| `/my_id` | anyone | Replies with your numeric Telegram ID (needed for the private code menus). If the reply starts with `False,` the bot doesn't recognise your username, but the number is still right. |
| `/stat <restaurant> [from DD.MM.YYYY] [till DD.MM.YYYY]` | anyone who can message the bot | Shows how often each error code occurred for one restaurant. |
| `/pending [month] [year]` | team members | Lists *your* closed tickets that never got error/resolution codes and offers to fill them in now. |
| `/killyourself` | team members | **Stops the whole bot immediately**, for all restaurants. It stays off until someone starts it again on the server. |

### `/stat` – statistics for one restaurant

```text
/stat kfc woergl
/stat kfc woergl from 01.05.2024
/stat kfc woergl from 01.05.2024 till 31.05.2024
```

The bot replies like this (counts are per error code, most frequent first; tickets that never got a code are shown last as `NotGiven`):

```text
KFC WOERGL statistics
Start date: 1.5.2024
End date: 31.5.2024
Total amount of errors: 10 issues.

Error Code '0102': 5 occurrences - Kiosk did not start
Error Code '1201': 2 occurrences - HDD/SSD malfunction
Error Code 'NotGiven': 3 occurrences - Description not found
```

Rules to get it right:

- **Write the restaurant name in lower case**, exactly like in the sheet (`kfc woergl`, not `KFC Wörgl`). If the name isn't found, the bot replies with the list of names it knows – copy one from there. Only restaurants that already have at least one ticket in the sheet are in that list.
- **Dates must have two digits for day and month and four for the year:** `01.05.2024`. A date in another shape such as `1.5.2024` is **silently ignored** and the bot uses "from the beginning" / "until today" instead. A date that doesn't exist (`31.02.2024`) gets an error message.
- Without `from`, the report starts at the very first ticket; without `till`, it ends today.

### `/pending` – tickets that still need codes

```text
/pending            ← this month
/pending 7          ← July of this year
/pending 7 2024     ← July 2024
```

The bot lists your closed tickets for that month which have no codes and asks **Yes ✅ / Nope 🚫**. On *Yes* it walks you through the same code menus as above, one ticket after another. Each question names the restaurant, date and time of the ticket.

If everything is filled in you get: *"All tickets for selected month were filled with error and resolution codes. Great job!"*

Two caveats – see [Troubleshooting → Known limitations](troubleshooting.md#known-limitations): `/pending` and `/killyourself` only know a fixed list of five people, and `/pending` without arguments may show the month in which the bot was last *started* rather than the current month. When in doubt, give the month and year explicitly.

---

## Cheat sheet

| I want to… | I write… | Where |
|---|---|---|
| Report a problem | normal text | restaurant group |
| Take an issue (stop the escalation) | anything, e.g. `on it` | restaurant group |
| Close an issue | `done` / `erledigt` (second message if it was your first) | restaurant group |
| Dismiss a false alarm | `not an issue` or `lock` (nothing else in the message) | restaurant group |
| Fill in error and fix | tap the buttons | private chat with the main bot |
| Fix up old tickets | `/pending 7 2024` | private chat with the main bot |
| See error statistics | `/stat kfc woergl from 01.05.2024` | private chat with the main bot |
| Find my Telegram ID | `/my_id` | private chat with the main bot |
