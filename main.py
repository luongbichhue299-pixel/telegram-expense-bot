import datetime
import pytz
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import TELEGRAM_BOT_TOKEN, ALLOWED_USER_ID
from handlers import start_command, today_command, handle_message
from logger import logger
import sheets

VN_TZ = pytz.timezone('Asia/Ho_Chi_Minh')

async def daily_summary_job(context):
    """Job gửi báo cáo hàng ngày vào lúc 23:00"""
    now = datetime.datetime.now(VN_TZ)
    date_str = now.strftime('%Y-%m-%d')
    
    months = ["January", "February", "March", "April", "May", "June", 
              "July", "August", "September", "October", "November", "December"]
    month_str = f"{months[now.month - 1]} {now.year}"
    
    # Lấy dữ liệu
    today_items, today_total = sheets.get_today_expenses(date_str)
    income, month_expense, balance = sheets.get_monthly_summary(month_str)
    
    # Xây dựng báo cáo
    report = f"📊 TỔNG KẾT CHI TIÊU HÀNG NGÀY\n📅 Hôm nay: {date_str}\n\n"
    
    if today_items:
        report += "📝 Chi tiết hôm nay:\n"
        for content, amount in today_items:
            report += f"  • {content}: {amount:,.0f}đ\n"
    else:
        report += "Hôm nay không có khoản chi tiêu nào.\n"
        
    report += f"\n━━━━━━━━━━━━━━━\n"
    report += f"💰 Tổng chi hôm nay: {today_total:,.0f}đ\n"
    report += f"📅 Tổng chi tháng ({month_str}): {month_expense}\n"
    report += f"⚖️ Dư nợ thu chi: {balance}\n"
    
    try:
        await context.bot.send_message(chat_id=ALLOWED_USER_ID, text=report)
        logger.info("Đã gửi báo cáo ngày thành công.")
    except Exception as e:
        logger.error(f"Lỗi khi gửi báo cáo ngày: {e}")

def main():
    logger.info("Đang khởi động bot...")
    
    # Tạo ứng dụng bot
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Đăng ký handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", start_command))
    application.add_handler(CommandHandler("today", today_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Đăng ký job hàng ngày lúc 23:00 GMT+7
    target_time = datetime.time(hour=23, minute=0, tzinfo=VN_TZ)
    application.job_queue.run_daily(daily_summary_job, time=target_time)
    
    # Chạy bot (polling)
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
