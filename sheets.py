import gspread
from google.oauth2.service_account import Credentials
import json
import base64
import os
from config import SPREADSHEET_ID, SHEET_NAME, GOOGLE_CREDENTIALS_BASE64
from logger import logger

# Các scope cần thiết để truy cập Google Sheets
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_gspread_client():
    try:
        if GOOGLE_CREDENTIALS_BASE64:
            # Decode từ biến môi trường (dùng trên Railway)
            creds_json = base64.b64decode(GOOGLE_CREDENTIALS_BASE64).decode('utf-8')
            creds_dict = json.loads(creds_json)
            credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        else:
            # Đọc từ file cục bộ
            if not os.path.exists("credentials.json"):
                logger.error("Không tìm thấy credentials.json và biến GOOGLE_CREDENTIALS_BASE64.")
                return None
            credentials = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
        
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        logger.error(f"Lỗi khi xác thực Google Sheets: {e}")
        return None

def setup_sheet(worksheet):
    """
    Format sheet 'Chi tiêu' nếu nó trống
    """
    if len(worksheet.get_all_values()) == 0:
        headers = ["Ngày gửi tin", "Nội dung chi tiêu", "Số tiền chi tiêu"]
        worksheet.append_row(headers)
        
        # Format header: nền xanh đậm, chữ trắng, in đậm, căn giữa
        worksheet.format("A1:C1", {
            "backgroundColor": {"red": 0.0, "green": 0.2, "blue": 0.4},
            "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "bold": True},
            "horizontalAlignment": "CENTER"
        })
        
        # Không thể set chiều rộng cột qua format đơn giản, bỏ qua hoặc dùng batch_update (phức tạp)
        # Sẽ ưu tiên append dữ liệu đúng trước.

def get_expense_worksheet():
    client = get_gspread_client()
    if not client:
        return None
    try:
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        try:
            worksheet = spreadsheet.worksheet(SHEET_NAME)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows="1000", cols="5")
            setup_sheet(worksheet)
        return worksheet
    except Exception as e:
        logger.error(f"Lỗi khi truy cập sheet '{SHEET_NAME}': {e}")
        return None

def get_payment_worksheet():
    client = get_gspread_client()
    if not client:
        return None
    try:
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet("Payment")
        return worksheet
    except Exception as e:
        logger.error(f"Lỗi khi truy cập sheet 'Payment': {e}")
        return None

def add_expense(date_str: str, content: str, amount: int) -> bool:
    """Ghi một khoản chi tiêu vào Google Sheets"""
    ws = get_expense_worksheet()
    if not ws:
        return False
    
    try:
        # Cột C tự động hiển thị số đúng định dạng do thiết lập trong Google Sheets, 
        # hoặc ta ghi string số tiền format, nhưng tốt nhất cứ ghi int.
        # Format số tiền để hiển thị đẹp có dấu phẩy nếu muốn. Nhưng yêu cầu: "định dạng số #,##0 đ"
        # Nên cứ truyền int, sau đó có thể set format sau nếu cần, hoặc người dùng tự set cột C trên Sheets.
        ws.append_row([date_str, content, amount])
        return True
    except Exception as e:
        logger.error(f"Lỗi khi ghi chi tiêu: {e}")
        return False

def get_today_expenses(date_prefix: str) -> tuple[list, int]:
    """
    Lấy danh sách chi tiêu và tổng tiền trong ngày.
    date_prefix dạng YYYY-MM-DD
    """
    ws = get_expense_worksheet()
    if not ws:
        return [], 0
    
    try:
        all_records = ws.get_all_values()
        today_items = []
        total = 0
        
        # Bỏ qua header
        for row in all_records[1:]:
            if len(row) >= 3 and row[0].startswith(date_prefix):
                content = row[1]
                try:
                    amount = int(row[2].replace(',', '').replace('.', '').replace(' đ', '').replace('đ', ''))
                except ValueError:
                    amount = 0
                today_items.append((content, amount))
                total += amount
                
        return today_items, total
    except Exception as e:
        logger.error(f"Lỗi khi lấy chi tiêu hôm nay: {e}")
        return [], 0

def get_monthly_summary(month_str: str) -> tuple[str, str, str]:
    """
    Đọc sheet Payment tìm dòng có tháng = month_str (VD: April 2026) ở cột F.
    Trả về (Tổng chi tháng, Dư nợ thu chi) (Bỏ qua thu nhập vì báo cáo chỉ yêu cầu hiển thị:
    - Tổng chi tháng
    - Dư nợ thu chi
    Trả về Tuple[Thu nhập, Tổng chi, Dư nợ] để đủ dữ liệu (tất cả là string đã format từ sheet)
    """
    ws = get_payment_worksheet()
    if not ws:
        return ("0", "0", "0")
    
    try:
        # Lấy tất cả dữ liệu từ các cột liên quan
        # Cột F: index 5, G: 6, H: 7, I: 8
        all_records = ws.get_all_values()
        for row in all_records:
            if len(row) > 8 and row[5].strip() == month_str:
                income = row[6].strip()
                expense = row[7].strip()
                balance = row[8].strip()
                return (income, expense, balance)
        
        return ("0", "0", "0")
    except Exception as e:
        logger.error(f"Lỗi khi lấy tổng kết tháng: {e}")
        return ("0", "0", "0")
