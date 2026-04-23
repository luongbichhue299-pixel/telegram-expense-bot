import os
import sys
from dotenv import load_dotenv
from logger import logger

load_dotenv()

# Lấy các biến môi trường
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_ID = os.getenv("ALLOWED_USER_ID")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME", "Chi tiêu")
GOOGLE_CREDENTIALS_BASE64 = os.getenv("GOOGLE_CREDENTIALS_BASE64")

# Validate các biến bắt buộc
missing_vars = []
if not TELEGRAM_BOT_TOKEN:
    missing_vars.append("TELEGRAM_BOT_TOKEN")
if not ALLOWED_USER_ID:
    missing_vars.append("ALLOWED_USER_ID")
else:
    try:
        ALLOWED_USER_ID = int(ALLOWED_USER_ID)
    except ValueError:
        logger.error("ALLOWED_USER_ID phải là một số nguyên.")
        sys.exit(1)

if not SPREADSHEET_ID:
    missing_vars.append("SPREADSHEET_ID")

if missing_vars:
    logger.error(f"Thiếu các biến môi trường bắt buộc: {', '.join(missing_vars)}")
    logger.error("Vui lòng kiểm tra file .env hoặc cấu hình trên Railway.")
    sys.exit(1)

logger.info("Đã tải cấu hình thành công.")
