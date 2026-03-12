import os
import sys
import json
import gspread
import requests
from google.oauth2.service_account import Credentials

TELEGRAM_TOKEN    = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID  = os.environ["TELEGRAM_CHAT_ID"]
SPREADSHEET_ID    = os.environ["SPREADSHEET_ID"]
GOOGLE_CREDS_JSON = os.environ["GOOGLE_CREDS_JSON"]

SHEET_NAME = "Загадки"
SITE_URL   = "https://saturn-kassiel.github.io/Kids-site/#riddles"

COL_RIDDLE = 1
COL_ANSWER = 2
COL_IMAGE  = 3
COL_POSTED = 4

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


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
    all_rows = sheet.get_all_values()
    for i, row in enumerate(all_rows[1:], start=2):
        riddle = row[COL_RIDDLE - 1].strip() if len(row) > COL_RIDDLE - 1 else ""
        answer = row[COL_ANSWER - 1].strip() if len(row) > COL_ANSWER - 1 else ""
        image  = row[COL_IMAGE - 1].strip()  if len(row) > COL_IMAGE - 1  else ""
        posted = row[COL_POSTED - 1].strip() if len(row) > COL_POSTED - 1 else ""
        if riddle and answer and posted.upper() != "TRUE":
            return i, riddle, answer, image
    return None, None, None, None


def mark_posted(sheet, row_index):
    sheet.update_cell(row_index, COL_POSTED, "TRUE")


def build_caption(riddle: str, answer: str) -> str:
    link = f'<a href="{SITE_URL}">Жми</a> 🔗 <a href="{SITE_URL}">загадки здесь</a>'
    return (
        f"<b>ЗАГАДКА</b>\n\n"
        f"{riddle}\n\n"
        f"<tg-spoiler>💡 Ответ: {answer}</tg-spoiler>\n\n"
        f"{link}"
    )


def send_photo_with_spoiler(image_url: str, caption: str):
    print(f"🖼 Отправляю фото: {image_url}", flush=True)
    print(f"📝 Длина caption: {len(caption)} символов", flush=True)
    resp = requests.post(f"{BASE_URL}/sendPhoto", json={
        "chat_id":     TELEGRAM_CHAT_ID,
        "photo":       image_url,
        "caption":     caption,
        "parse_mode":  "HTML",
        "has_spoiler": True,
    })
    print(f"📬 Telegram ответ: {resp.status_code} {resp.text}", flush=True)
    resp.raise_for_status()
    return resp.json()


def send_message(text: str):
    print(f"📝 Отправляю текст, длина: {len(text)}", flush=True)
    resp = requests.post(f"{BASE_URL}/sendMessage", json={
        "chat_id":    TELEGRAM_CHAT_ID,
        "text":       text,
        "parse_mode": "HTML",
    })
    print(f"📬 Telegram ответ: {resp.status_code} {resp.text}", flush=True)
    resp.raise_for_status()
    return resp.json()


def main():
    sheet = get_sheet()
    row_index, riddle, answer, image_url = get_next_riddle(sheet)

    if riddle is None:
        print("✅ Все загадки уже опубликованы!", flush=True)
        return

    print(f"📌 Публикую строку {row_index}", flush=True)
    print(f"📖 Загадка: {riddle[:60]}", flush=True)
    print(f"💡 Ответ: {answer}", flush=True)
    print(f"🖼 URL: {image_url}", flush=True)

    caption = build_caption(riddle, answer)

    if image_url:
        send_photo_with_spoiler(image_url, caption)
    else:
        send_message(caption)

    mark_posted(sheet, row_index)
    print("✅ Готово!", flush=True)


if __name__ == "__main__":
    main()
