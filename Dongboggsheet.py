import gspread
from oauth2client.service_account import ServiceAccountCredentials
import sqlite3
import pandas as pd

def dong_bo_sheet1():
    try:
        # 1. Cấu hình kết nối
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
        client = gspread.authorize(creds)

        # 2. Mở Sheet và lấy toàn bộ dữ liệu thô
        # Thay "Tên File..." bằng tên file thật của bạn
        sheet = client.open("3.Quỹ đầu tư").get_worksheet(1)
        raw_data = sheet.get_all_values()

        if not raw_data:
            print("Sheet rỗng, không có dữ liệu để đồng bộ.")
            return

        # 3. Tối ưu hóa với Pandas
        # Chúng ta tạo DataFrame mà không chỉ định header (mặc định sẽ là 0, 1, 2, 3...)
        df = pd.DataFrame(raw_data)
        df.columns = [f"Col_{i}" for i in range(1, len(df.columns) + 1)]
        # Thêm cột row_id vào đầu bảng, đánh số từ 1 đến hết
        df.insert(0, 'row_id', range(1, len(df) + 1))

        # 4. Ghi vào SQLite
        with sqlite3.connect('database.db') as conn:
            # Ghi đè toàn bộ bảng 'my_table'
            # index=False vì chúng ta đã tự tạo cột row_id rồi
            df.to_sql('ThongTinQuy', conn, if_exists='replace', index=False)
        
        print(f"Đã đồng bộ thành công {len(df)} hàng và {len(df.columns)-1} cột.")

    except Exception as e:
        print(f"Có lỗi xảy ra: {e}")

if __name__ == "__main__":
    dong_bo_sheet1()

def dong_bo_sheet0():
    try:
        # 1. Cấu hình kết nối
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
        client = gspread.authorize(creds)

        # 2. Mở Sheet và lấy toàn bộ dữ liệu thô
        # Thay "Tên File..." bằng tên file thật của bạn
        sheet = client.open("3.Quỹ đầu tư").get_worksheet(0)
        raw_data = sheet.get_all_values()

        if not raw_data:
            print("Sheet rỗng, không có dữ liệu để đồng bộ.")
            return

        # 4. ĐƯA VÀO PANDAS VÀ XỬ LÝ LỖI TIÊU ĐỀ
        # Chúng ta lấy hàng đầu tiên làm tiêu đề tạm thời
        df = pd.DataFrame(raw_data)
    
        # Dòng này cực kỳ quan trọng: 
        # Nó sẽ đặt lại tên cột là 0, 1, 2, 3... để tránh lỗi trùng tên ('', 'STT', 'STT')
        # Sau đó ta có thể đặt hàng đầu tiên làm dữ liệu nếu muốn, hoặc xóa nó đi.
        header = raw_data[0]
        df.columns = [f"Col_{i}_{name}" if name == '' or header.count(name) > 1 else name 
                  for i, name in enumerate(header)]
    
        # Bỏ hàng đầu tiên đi vì nó đã nằm ở phần tiêu đề cột (df.columns)
        df = df.iloc[1:]

        # 5. ĐẨY VÀO SQLITE
        conn = sqlite3.connect('database.db')
    
        # if_exists='replace' đảm bảo mỗi lần chạy là một lần "Paste" mới hoàn toàn
        df.to_sql('user_report', conn, if_exists='replace', index=False)
    
        conn.close()
        print("Đã 'Copy-Paste' toàn bộ dữ liệu vào SQLite thành công!")
    except Exception as e:
        print(f"Có lỗi xảy ra: {e}")
        
dong_bo_sheet0()
