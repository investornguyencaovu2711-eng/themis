import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.graph_objects as go

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
    df['Giá trị quỹ'] = pd.to_numeric(df['Giá trị quỹ'].apply(clean_currency), errors='coerce')
    df['Vốn chủ sở hữu'] = pd.to_numeric(df['Vốn chủ sở hữu'].apply(clean_currency), errors='coerce')

    # Loại bỏ các dòng bị trống (NaN) sau khi chuyển đổi
    df = df.dropna(subset=['Ngày', 'Giá trị quỹ', 'Vốn chủ sở hữu'])

    # Chuyển sang đơn vị triệu VNĐ để biểu đồ thoáng hơn
    df['Giá trị quỹ triệu'] = df['Giá trị quỹ'] / 1_000_000
    df['Vốn chủ sở hữu triệu'] = df['Vốn chủ sở hữu'] / 1_000_000

except KeyError as e:
    print(f"Lỗi: Không tìm thấy cột {e}. Hãy kiểm tra lại tên cột ở hàng 1 trên Sheets.")
    exit()

# --- 4. VẼ BIỂU ĐỒ PLOTLY ---
fig = go.Figure()

# Đường Giá trị quỹ
fig.add_trace(go.Scatter(
    x=df['Ngày'],
    y=df['Giá trị quỹ triệu'],
    mode='lines+markers',
    name='Giá trị quỹ',
    line=dict(color='green', width=2),
    marker=dict(size=7),
    hovertemplate='Ngày: %{x|%d/%m/%Y}<br>Giá trị: %{y:,.2f} triệu VNĐ'
))

# Đường Vốn chủ sở hữu
fig.add_trace(go.Scatter(
    x=df['Ngày'],
    y=df['Vốn chủ sở hữu triệu'],
    mode='lines+markers',
    name='Vốn chủ sở hữu',
    line=dict(color='orange', width=2, dash='dash'),
    marker=dict(size=7),
    hovertemplate='Ngày: %{x|%d/%m/%Y}<br>Vốn CSH: %{y:,.2f} triệu VNĐ'
))

# Cấu hình giao diện biểu đồ
fig.update_layout(
    title='Theo dõi Biến động Quỹ và Vốn Chủ Sở Hữu',
    xaxis_title='Thời gian',
    yaxis_title='Giá trị (Triệu VNĐ)',
    hovermode='x unified',
    template='plotly_white',
    legend=dict(x=0.01, y=0.99),
    margin=dict(l=40, r=40, t=60, b=40)
)

# Hiển thị biểu đồ
fig.write_html("bieudovonchusohuu.html")
fig.show()
