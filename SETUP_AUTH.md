# Hướng dẫn Setup Authentication (Supabase + Vercel)

## Bước 1: Tạo Supabase Project (miễn phí)

1. Mở trình duyệt, vào **https://supabase.com**
2. Click **Start your project** → đăng nhập bằng GitHub
3. Click **New Project**
   - **Organization**: chọn org mặc định (hoặc tạo mới)
   - **Project name**: `uvm-gen` (hoặc tên bất kỳ)
   - **Database Password**: tạo password mạnh → **lưu lại**
   - **Region**: chọn **Southeast Asia (Singapore)** cho nhanh
   - **Pricing plan**: **Free** (đã chọn sẵn)
4. Click **Create new project** → đợi 1-2 phút để setup xong

## Bước 2: Lấy Supabase Keys

1. Trong Supabase Dashboard, vào **Project Settings** (icon bánh răng ở sidebar trái, phía dưới cùng)
2. Click **API** (trong menu bên trái)
3. Bạn sẽ thấy:

   **Project URL:**
   ```
   https://abcdefghijk.supabase.co
   ```
   → Copy giá trị này. Đây là `SUPABASE_URL`

   **Project API Keys → anon public:**
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxx...
   ```
   → Copy giá trị này. Đây là `SUPABASE_ANON_KEY`

## Bước 3: Chạy Migration SQL

1. Trong Supabase Dashboard, click **SQL Editor** (icon ở sidebar trái)
2. Click **New query**
3. Mở file `supabase_migration.sql` trong project UVM_Gen
4. Copy **toàn bộ nội dung** file đó, paste vào SQL Editor
5. Click **Run** (hoặc Ctrl+Enter)
6. Chờ cho đến khi thấy **Success. No rows returned** - nghĩa là đã tạo xong tables

**Kiểm tra:** Vào **Table Editor** (sidebar trái) → bạn sẽ thấy 3 tables:
- `profiles`
- `messages`
- `download_log`

## Bước 4: Cấu hình Auth trên Supabase

1. Vào **Authentication** (sidebar trái)
2. Click **Providers** (menu trái)
3. Đảm bảo **Email** provider đang **Enabled** (mặc định đã bật)
4. (Tùy chọn) Bỏ tick **Confirm email** nếu muốn user đăng ký xong dùng ngay, không cần confirm email:
   - Vào **Authentication** → **Settings** → **Email Auth**
   - Tắt **Enable email confirmations**

## Bước 5: Thêm Environment Variables trên Vercel

1. Mở **https://vercel.com** → đăng nhập
2. Vào project **uvm-gen** (click vào tên project)
3. Click tab **Settings** (thanh menu trên cùng)
4. Click **Environment Variables** (menu trái)
5. Thêm từng biến:

   | Key | Value | Environment |
   |-----|-------|-------------|
   | `SUPABASE_URL` | `https://abcdefghijk.supabase.co` | Production, Preview, Development |
   | `SUPABASE_ANON_KEY` | `eyJhbGci...your-key` | Production, Preview, Development |

   Cách thêm:
   - **Key**: nhập `SUPABASE_URL`
   - **Value**: paste URL từ Bước 2
   - Tick cả 3: **Production**, **Preview**, **Development**
   - Click **Save**
   - Lặp lại cho `SUPABASE_ANON_KEY`

6. Sau khi thêm xong, bạn sẽ thấy 2 variables trong danh sách

## Bước 6: Redeploy

Sau khi thêm env vars, cần redeploy để app nhận được keys mới:

**Cách 1 - Từ Vercel Dashboard:**
1. Vào tab **Deployments**
2. Tìm deployment mới nhất → click dấu **...** (3 chấm) bên phải
3. Click **Redeploy**

**Cách 2 - Từ terminal:**
```bash
cd /Users/phamkhang/Documents/CursorAI/UVM_Gen
npx vercel --yes --prod
```

## Bước 7: Kiểm tra

1. Mở **https://uvm-gen.vercel.app**
2. Bạn sẽ thấy nút **Sign In** ở góc phải header
3. Click **Sign In** → chuyển tab **Create Account**
4. Điền thông tin → tạo account
5. Đăng nhập xong:
   - Avatar hiện ở header
   - Nút chat (feedback) hiện ra
   - Download ZIP hoạt động

## Kiểm tra nhanh qua API

```bash
curl -s https://uvm-gen.vercel.app/api/config
```

Nếu setup đúng, bạn sẽ thấy:
```json
{
  "supabase_url": "https://abcdefghijk.supabase.co",
  "supabase_anon_key": "eyJhbGci...",
  "auth_enabled": true
}
```

Nếu chưa setup, sẽ thấy:
```json
{
  "supabase_url": "",
  "supabase_anon_key": "",
  "auth_enabled": false
}
```

## Tạo Admin Account

Sau khi tạo account đầu tiên, để set nó làm admin:

1. Vào **Supabase Dashboard** → **Table Editor** → bảng **profiles**
2. Tìm row của bạn (theo email)
3. Click vào field **role** → đổi từ `user` thành `admin`
4. Nhấn Enter để save

Admin có thể đọc tất cả messages từ users trong bảng `messages`.
