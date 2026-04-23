from telegram import Update
from telegram.ext import ContextTypes
import pytz
from datetime import datetime
from functools import wraps

from config import ALLOWED_USER_ID
from logger import logger
from parser_utils import parse_expense_line
import sheets

# Múi giờ Việt Nam
VN_TZ = pytz.timezone('Asia/Ho_Chi_Minh')

def restricted(func):
    """Decorator để hạn chế quyền truy cập bot chỉ cho ALLOWED_USER_ID"""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id != ALLOWED_USER_ID:
            logger.warning(f"Người dùng trái phép truy cập: {user_id} - {update.effective_user.username}")
            await update.message.reply_text("⛔ Bạn không có quyền sử dụng bot này.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

@restricted
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /start và /help"""
    help_text = (
        "🤖 **Bot Chi Tiêu Cá Nhân**\n\n"
        "Hướng dẫn ghi chi tiêu:\n"
        "Gửi tin nhắn với định dạng: `<nội dung> <số tiền>`\n\n"
        "Ví dụ hợp lệ:\n"
        "- `cafe sáng 25000`\n"
        "- `ăn trưa 85,000`\n"
        "- `grab 35.000`\n"
        "- `bún bò 45k`\n\n"
        "Bạn có thể gửi nhiều dòng trong 1 tin nhắn để ghi nhiều khoản.\n\n"
        "Các lệnh hỗ trợ:\n"
        "/start, /help - Hiển thị hướng dẫn này\n"
        "/today - Xem tổng chi tiêu hôm nay\n"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

@restricted
async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /today"""
    now = datetime.now(VN_TZ)
    date_str = now.strftime('%Y-%m-%d')
    
    items, total = sheets.get_today_expenses(date_str)
    
    if not items:
        await update.message.reply_text("Chưa có chi tiêu nào được ghi hôm nay.")
        return
        
    response = f"📅 Chi tiêu hôm nay ({date_str}):\n\n"
    for content, amount in items:
        response += f"  • {content}: {amount:,.0f}đ\n"
        
    response += f"\n━━━━━━━━━━━━━━━\n💰 Tổng: {total:,.0f}đ"
    
    await update.message.reply_text(response)

@restricted
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý tin nhắn ghi chi tiêu"""
    text = update.message.text
    lines = text.split('\n')
    
    success_items = []
    failed_lines = []
    
    now = datetime.now(VN_TZ)
    date_str = now.strftime('%Y-%m-%d %H:%M')
    
    for line in lines:
        if not line.strip():
            continue
            
        parsed = parse_expense_line(line)
        if parsed:
            content, amount = parsed
            success = sheets.add_expense(date_str, content, amount)
            if success:
                success_items.append((content, amount))
                logger.info(f"Ghi thành công: {content} - {amount}")
            else:
                failed_lines.append((line, "Lỗi khi ghi vào Google Sheets"))
        else:
            failed_lines.append((line, "Sai định dạng"))
            
    # Xây dựng tin nhắn phản hồi
    response_parts = []
    
    if success_items:
        part = f"💾 Đã ghi {len(success_items)} khoản chi tiêu:\n"
        for content, amount in success_items:
            part += f"  ✅ {content}: {amount:,.0f}đ\n"
        response_parts.append(part)
        
    if failed_lines:
        if not success_items:
            response_parts.append("❌ Không nhận ra định dạng chi tiêu.\n📝 Hãy gửi theo dạng: `<nội dung> <số tiền>`")
        else:
            part = f"⚠️ Có lỗi với {len(failed_lines)} dòng sau:\n"
            for line, error in failed_lines:
                part += f"  ❓ `{line}`\n"
            response_parts.append(part)
            
    if not response_parts:
        response_parts.append("Không có dòng nội dung hợp lệ nào.")
        
    await update.message.reply_text("\n\n".join(response_parts), parse_mode='Markdown')
