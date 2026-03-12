import os, json
import gspread, requests
from google.oauth2.service_account import Credentials

TELEGRAM_TOKEN    = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID  = os.environ["TELEGRAM_CHAT_ID"]
SPREADSHEET_ID    = os.environ["SPREADSHEET_ID"]
GOOGLE_CREDS_JSON = os.environ["GOOGLE_CREDS_JSON"]
SHEET_NAME = "Загадки"
SITE_URL   = "https://saturn-kassiel.github.io/Kids-site/#riddles"
BASE_URL   = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

def get_sheet():
    creds = Credentials.from_service_account_info(
        json.loads(GOOGLE_CREDS_JSON),
        scopes=["https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive.readonly"])
    return gspread.authorize(creds).open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

def get_next_riddle(sheet):
    for i, row in enumerate(sheet.get_all_values()[1:], start=2):
        r = [c.strip() for c in (row + ["","","",""])[:4]]
        if r[0] and r[1] and r[3].upper() != "TRUE":
            return i, r[0], r[1], r[2]
    return None, None, None, None

def build_caption(riddle, answer):
    link = f'<a href="{SITE_URL}">Жми</a> 🔗 <a href="{SITE_URL}">загадки здесь</a>'
    return f"<b>ЗАГАДКА</b>\n\n{riddle}\n\n<tg-spoiler>💡 Ответ: {answer}</tg-spoiler>\n\n{link}"

def main():
    sheet = get_sheet()
    row_index, riddle, answer, image_url = get_next_riddle(sheet)
    if riddle is None:
        print("Все загадки опубликованы!", flush=True)
        return

    print(f"Строка: {row_index}", flush=True)
    print(f"URL картинки: [{image_url}]", flush=True)
    caption = build_caption(riddle, answer)

    if image_url:
        # Скачиваем картинку и отправляем как файл
        img_resp = requests.get(image_url)
        print(f"Скачивание картинки: {img_resp.status_code}", flush=True)
        img_resp.raise_for_status()
        filename = image_url.split("/")[-1]
        resp = requests.post(f"{BASE_URL}/sendPhoto", 
            data={
                "chat_id":     TELEGRAM_CHAT_ID,
                "caption":     caption,
                "parse_mode":  "HTML",
                "has_spoiler": "true",
            },
            files={"photo": (filename, img_resp.content, "image/png")})
    else:
        resp = requests.post(f"{BASE_URL}/sendMessage", json={
            "chat_id": TELEGRAM_CHAT_ID, "text": caption, "parse_mode": "HTML"})

    print(f"Telegram: {resp.status_code} {resp.text[:200]}", flush=True)
    resp.raise_for_status()
    sheet.update_cell(row_index, 4, "TRUE")
    print("Готово!", flush=True)

if __name__ == "__main__":
    main()
