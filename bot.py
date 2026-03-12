import os
import json
import gspread
import requests
from google.oauth2.service_account import Credentials

# ─── Config ───────────────────────────────────────────────────────────────────

TELEGRAM_TOKEN   = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]   # например: @mychannel или -100xxxxxxxxx
SPREADSHEET_ID   = os.environ["SPREADSHEET_ID"]     # ID таблицы из URL
GOOGLE_CREDS_JSON = os.environ["GOOGLE_CREDS_JSON"] # JSON сервисного аккаунта (строкой)

SHEET_NAME = "Загадки"  # имя листа в таблице

# Колонки (1-based)
COL_RIDDLE  = 1   # A — текст загадки
COL_ANSWER  = 2   # B — ответ
COL_IMAGE   = 3   # C — ссылка на картинку (необязательно)
COL_POSTED  = 4   # D — статус (TRUE / пусто)

# ─── Google Sheets ─────────────────────────────────────────────────────────────

def get_sheet():
    creds_dict = json.loads(GOOGLE_CREDS_JSON)
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)


def get_next_riddle(sheet):
    """Возвращает (row_index, riddle, answer, image_url) первой незапощенной строки."""
    all_rows = sheet.get_all_values()
    for i, row in enumerate(all_rows[1:], start=2):  # пропускаем заголовок
        riddle  = row[COL_RIDDLE - 1].strip()  if len(row) > COL_RIDDLE - 1  else ""
        answer  = row[COL_ANSWER - 1].strip()  if len(row) > COL_ANSWER - 1  else ""
        image   = row[COL_IMAGE - 1].strip()   if len(row) > COL_IMAGE - 1   else ""
        posted  = row[COL_POSTED - 1].strip()  if len(row) > COL_POSTED - 1  else ""

        if riddle and answer and posted.upper() != "TRUE":
            return i, riddle, answer, image

    return None, None, None, None


def mark_posted(sheet, row_index):
    sheet.update_cell(row_index, COL_POSTED, "TRUE")

# ─── Telegram ──────────────────────────────────────────────────────────────────

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


def build_text(riddle: str, answer: str) -> str:
    return (
        f"🧩 <b>Загадка дня</b>\n\n"
        f"{riddle}\n\n"
        f"<tg-spoiler>💡 Ответ: {answer}</tg-spoiler>"
    )


def send_message(text: str):
    resp = requests.post(f"{BASE_URL}/sendMessage", data={
        "chat_id":    TELEGRAM_CHAT_ID,
        "text":       text,
        "parse_mode": "HTML",
    })
    resp.raise_for_status()
    return resp.json()


def send_photo(image_url: str, caption: str):
    resp = requests.post(f"{BASE_URL}/sendPhoto", data={
        "chat_id":    TELEGRAM_CHAT_ID,
        "photo":      image_url,
        "caption":    caption,
        "parse_mode": "HTML",
    })
    resp.raise_for_status()
    return resp.json()

# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    sheet = get_sheet()
    row_index, riddle, answer, image_url = get_next_riddle(sheet)

    if riddle is None:
        print("✅ Все загадки уже опубликованы!")
        return

    print(f"📌 Публикую строку {row_index}: {riddle[:50]}...")

    text = build_text(riddle, answer)

    if image_url:
        send_photo(image_url, text)
    else:
        send_message(text)

    mark_posted(sheet, row_index)
    print("✅ Опубликовано и отмечено в таблице.")


if __name__ == "__main__":
    main()
