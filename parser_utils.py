import re
from typing import Tuple, Optional

def parse_expense_line(line: str) -> Optional[Tuple[str, int]]:
    """
    Phân tích một dòng tin nhắn thành (nội dung, số tiền).
    Ví dụ:
    - cafe sáng 25000 -> ("cafe sáng", 25000)
    - ăn trưa 85,000 -> ("ăn trưa", 85000)
    - grab 35.000 -> ("grab", 35000)
    - bún bò 45k -> ("bún bò", 45000)
    - trà sữa 50K -> ("trà sữa", 50000)
    Trả về None nếu không đúng định dạng.
    """
    line = line.strip()
    if not line:
        return None

    # Biểu thức chính quy:
    # ^(.*?)       : Lấy nội dung, non-greedy
    # \s+          : Ít nhất 1 khoảng trắng ngăn cách
    # (            : Bắt đầu group bắt số tiền
    #  (?:\d{1,3}(?:[.,]\d{3})*|\d+) : Các định dạng số 100, 1.000, 10,000, 10000
    #  [kK]?       : Có thể có chữ k hoặc K ở cuối
    # )$           : Kết thúc chuỗi
    pattern = r'^(.*?)\s+((?:\d{1,3}(?:[.,]\d{3})*|\d+)[kK]?)$'
    match = re.match(pattern, line)
    
    if not match:
        return None

    content = match.group(1).strip()
    amount_str = match.group(2).strip()

    if not content:
        return None

    # Xử lý chuỗi số tiền để chuyển về int
    amount_str = amount_str.lower()
    multiplier = 1
    if amount_str.endswith('k'):
        multiplier = 1000
        amount_str = amount_str[:-1]

    # Loại bỏ dấu chấm và dấu phẩy
    amount_str = amount_str.replace(',', '').replace('.', '')

    try:
        amount = int(amount_str) * multiplier
        if amount <= 0:
            return None
        return content, amount
    except ValueError:
        return None
