import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CẤU HÌNH KẾT NỐI ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
client = gspread.authorize(creds)

# --- 2. MỞ FILE VÀ XỬ LÝ ---
try:
    # Mở file và lấy dữ liệu
    sh = client.open("1.Nạp Tiền và Báo cáo quỹ")
    worksheet = sh.worksheet("Báo cáo quỹ")
    range_values = worksheet.get("M1:O5")
    
    # Chuyển thành DataFrame
    # Lưu ý: header=None vì ta sẽ lấy trực tiếp dữ liệu từ range
    df = pd.DataFrame(range_values)
    
    # Tạo bảng HTML cơ bản
    html_table = df.to_html(index=False, header=False)
    
    # Bọc vào khung HTML hoàn chỉnh
    html_content = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title> </title>
        <style>
            table {{ border-collapse: collapse; width: 100%; margin: 0px; }}
            td {{ border: 1px solid black; padding: 8px; text-align: center; }}
        </style>
    </head>
    <body>
        <h2></h2>
        {html_table}
    </body>
    </html>
    """
    
    # Ghi file
    with open("thongtintongthecuaquy.html", "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print("Thành công! Hãy mở file report.html để xem kết quả.")

except Exception as e:
    print(f"Đã xảy ra lỗi: {e}")
