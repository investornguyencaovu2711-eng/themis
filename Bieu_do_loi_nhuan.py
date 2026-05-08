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

# ... (Các phần cấu hình kết nối và lấy dữ liệu giữ nguyên) ...

# --- 3. DỌN DẸP VÀ XỬ LÝ DỮ LIỆU ---
df.columns = df.columns.str.strip()

def clean_currency(value):
    if isinstance(value, str):
        return value.replace('.', '').replace('đ', '').replace(',', '').strip()
    return value

try:
    df['Ngày'] = pd.to_datetime(df['Ngày'], format='%d/%m/%Y', errors='coerce')
    df['Biên độ lãi'] = pd.to_numeric(df['Biên độ lãi'].apply(clean_currency), errors='coerce')
    df = df.dropna(subset=['Ngày', 'Biên độ lãi'])

    # Giữ nguyên đơn vị VND gốc
    df['Lãi'] = df['Biên độ lãi'].where(df['Biên độ lãi'] >= 0)
    df['Lỗ'] = df['Biên độ lãi'].where(df['Biên độ lãi'] < 0)

except KeyError as e:
    print(f"Lỗi: Không tìm thấy cột {e}")
    exit()

# --- 4. XỬ LÝ ĐIỂM GIAO NHAU (Để đường kẻ mượt mà tại điểm 0) ---
df['sign'] = np.sign(df['Biên độ lãi'])
sign_change = df['sign'].diff().fillna(0) != 0
change_indices = df.index[sign_change & (df.index != df.index[0])]

new_rows = []
for idx in change_indices:
    row_prev = df.loc[idx - 1]
    row_curr = df.loc[idx]
    y1, y2 = row_prev['Biên độ lãi'], row_curr['Biên độ lãi']
    if y2 != y1:
        t = -y1 / (y2 - y1)
        intersect_date = row_prev['Ngày'] + t * (row_curr['Ngày'] - row_prev['Ngày'])
        new_row = row_curr.copy()
        new_row['Ngày'] = intersect_date
        new_row['Biên độ lãi'] = 0
        new_rows.append(new_row)

df_extended = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True).sort_values('Ngày')
df_extended['Lãi'] = df_extended['Biên độ lãi'].mask(df_extended['Biên độ lãi'] < 0)
df_extended['Lỗ'] = df_extended['Biên độ lãi'].mask(df_extended['Biên độ lãi'] > 0)

# --- 5. VẼ BIỂU ĐỒ ---
fig = go.Figure()

# Định dạng hiển thị khi rà chuột: .2s hoặc phân cách dấu phẩy, thêm " đ"
# Ở đây dùng định dạng số nguyên có dấu phân cách: ",.0f"
hovertemplate_custom = "%{y:,.0f} đ<extra></extra>"

fig.add_trace(go.Scatter(
    x=df_extended['Ngày'], y=df_extended['Lỗ'],
    mode='lines', line=dict(color='#fc0303', width=2),
    name='Lỗ', hovertemplate=hovertemplate_custom
))

fig.add_trace(go.Scatter(
    x=df_extended['Ngày'], y=df_extended['Lãi'],
    mode='lines', line=dict(color='#198a19', width=2),
    name='Lãi', hovertemplate=hovertemplate_custom
))

fig.add_hline(y=0, line_dash="solid", line_color="#333", opacity=0.3)

# Cấu hình Layout
fig.update_layout(
    title='Biểu đồ Lợi nhuận Quỹ',
    xaxis_title='Thời gian',
    yaxis_title='VNĐ',
    hovermode='x unified',
    template='plotly_white',
    # Định dạng trục Y: dấu phẩy phân cách hàng nghìn (Plotly mặc định dùng dấu phẩy, 
    # nhưng bạn có thể tùy chỉnh nếu muốn dùng dấu chấm theo chuẩn VN)
    yaxis=dict(tickformat=",d") 
)

# Để đổi dấu phẩy thành dấu chấm theo chuẩn VN trong Plotly:
fig.update_layout(separators=',.')
fig.write_html("BieuDoLoiNhuan.html")
fig.show()
