import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.graph_objects as go
import numpy as np

# --- 1. CẤU HÌNH KẾT NỐI ---
# Đảm bảo file 'service_account.json' nằm cùng thư mục với file code này
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
client = gspread.authorize(creds)

# --- 2. MỞ FILE VÀ LẤY DỮ LIỆU ---
# Thay "Tên_File_Của_Bạn" bằng tên file Google Sheet thực tế
try:
    sh = client.open("4.Lưu trữ Lệnh và data")
    worksheet = sh.worksheet("Lưu trữ data quỹ")  # Lấy trang tính đầu tiên
    all_values = worksheet.get_all_values()
    
    # Tạo DataFrame từ dữ liệu thô
    df = pd.DataFrame(all_values[1:], columns=all_values[0])
except Exception as e:
    print(f"Không thể kết nối hoặc mở file: {e}")
    exit()

# --- 3. DỌN DẸP VÀ XỬ LÝ DỮ LIỆU ---

# Xóa khoảng trắng dư thừa trong tên các cột
df.columns = df.columns.str.strip()

# Hàm làm sạch các ký tự tiền tệ (. và đ)
def clean_currency(value):
    if isinstance(value, str):
        # Xóa dấu chấm, chữ 'đ', khoảng trắng và thay dấu phẩy thành rỗng
        return value.replace('.', '').replace('đ', '').replace(',', '').strip()
    return value

# Áp dụng làm sạch và chuyển sang kiểu số
try:
    # Chuyển cột Ngày sang định dạng datetime
    df['Ngày'] = pd.to_datetime(df['Ngày'], format='%d/%m/%Y', errors='coerce')
    
    # Làm sạch và chuyển cột giá trị sang số
    df['Biên độ lãi'] = pd.to_numeric(df['Biên độ lãi'].apply(clean_currency), errors='coerce')
   

    # Loại bỏ các dòng bị trống (NaN) sau khi chuyển đổi
    df = df.dropna(subset=['Ngày', 'Biên độ lãi'])

    # Chuyển sang đơn vị triệu VNĐ để biểu đồ thoáng hơn
    df['Biên độ lãi triệu'] = df['Biên độ lãi'] / 1_000_000

    # Tạo 2 cột mới dựa trên điều kiện
    df['Lãi'] = df['Biên độ lãi triệu'].where(df['Biên độ lãi triệu'] >= 0)
    df['Lỗ'] = df['Biên độ lãi triệu'].where(df['Biên độ lãi triệu'] < 0)

except KeyError as e:
    print(f"Lỗi: Không tìm thấy cột {e}. Hãy kiểm tra lại tên cột ở hàng 1 trên Sheets.")
    exit()

# --- 4. VẼ BIỂU ĐỒ PLOTLY ---
# 1. TÌM CÁC ĐIỂM GIAO NHAU VỚI TRỤC 0
# Xác định vị trí nơi dấu của giá trị thay đổi (từ + sang - hoặc ngược lại)
df['sign'] = np.sign(df['Biên độ lãi triệu'])
sign_change = df['sign'].diff().fillna(0) != 0
change_indices = df.index[sign_change & (df.index != df.index[0])]

new_rows = []
for idx in change_indices:
    # Lấy điểm trước và điểm hiện tại
    row_prev = df.loc[idx - 1]
    row_curr = df.loc[idx]
    
    # Tính toán tỷ lệ để tìm điểm t tại đó y = 0 (nội suy tuyến tính)
    # y = y1 + t * (y2 - y1) = 0  => t = -y1 / (y2 - y1)
    y1 = row_prev['Biên độ lãi triệu']
    y2 = row_curr['Biên độ lãi triệu']
    
    if y2 != y1:
        t = -y1 / (y2 - y1)
        # Tính ngày trung gian
        delta_time = row_curr['Ngày'] - row_prev['Ngày']
        intersect_date = row_prev['Ngày'] + t * delta_time
        
        # Tạo dòng mới tại điểm 0
        new_row = row_curr.copy()
        new_row['Ngày'] = intersect_date
        new_row['Biên độ lãi triệu'] = 0
        new_rows.append(new_row)

# 2. CHÈN ĐIỂM 0 VÀO DỮ LIỆU VÀ SẮP XẾP LẠI
df_extended = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
df_extended = df_extended.sort_values('Ngày').reset_index(drop=True)

# 3. TẠO DỮ LIỆU RIÊNG CHO ĐƯỜNG XANH VÀ ĐỎ
# Chúng ta dùng .mask() để giữ lại giá trị và gán NaN cho phần còn lại
# Quan trọng: Cả hai đường đều phải giữ lại các điểm y=0 để nối liền nhau
df_extended['Lãi'] = df_extended['Biên độ lãi triệu'].mask(df_extended['Biên độ lãi triệu'] < 0)
df_extended['Lỗ'] = df_extended['Biên độ lãi triệu'].mask(df_extended['Biên độ lãi triệu'] > 0)

# 4. VẼ BIỂU ĐỒ
fig = go.Figure()

# Vẽ vùng Lỗ (Màu đỏ)
fig.add_trace(go.Scatter(
    x=df_extended['Ngày'],
    y=df_extended['Lỗ'],
    mode='lines',
    line=dict(color='#fc0303', width=2), # Màu đỏ chuẩn Plotly
    name='Lỗ',
    connectgaps=False
))

# Vẽ vùng Lãi (Màu xanh)
fig.add_trace(go.Scatter(
    x=df_extended['Ngày'],
    y=df_extended['Lãi'],
    mode='lines',
    line=dict(color='#198a19', width=2), # Màu xanh chuẩn Plotly
    name='Lãi',
    connectgaps=False
))

# Đường tham chiếu y=0
fig.add_hline(y=0, line_dash="solid", line_color="#333", opacity=0.3)

# Cấu hình giao diện
fig.update_layout(
    title='Biểu đồ Lợi nhuận Quỹ',
    xaxis_title='Thời gian',
    yaxis_title='Triệu VNĐ',
    hovermode='x unified',
    template='plotly_white',
    showlegend=True
)


# Hiển thị biểu đồ
fig.write_html("BieuDoLoiNhuan.html")
fig.show()
