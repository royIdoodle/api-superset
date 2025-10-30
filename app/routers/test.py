from fastapi import APIRouter
from fastapi.responses import HTMLResponse


router = APIRouter()


@router.get("/upload", response_class=HTMLResponse)
def upload_form() -> str:
    # 简易测试页：POST 到 /images/upload
    return """
<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>图片上传测试</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif; padding: 24px; }
    .card { max-width: 720px; margin: 0 auto; border: 1px solid #ddd; border-radius: 8px; padding: 20px; }
    label { display: block; margin-top: 12px; font-weight: 600; }
    input, select { width: 100%; padding: 8px; margin-top: 6px; }
    button { margin-top: 16px; padding: 10px 16px; font-weight: 600; }
    pre { background: #f7f7f7; padding: 12px; white-space: pre-wrap; word-break: break-all; }
  </style>
  <script>
    async function handleSubmit(e) {
      e.preventDefault();
      const form = document.getElementById('uploadForm');
      const fd = new FormData(form);
      const resp = await fetch('/images/upload', { method: 'POST', body: fd });
      const text = await resp.text();
      try {
        const json = JSON.parse(text);
        document.getElementById('result').textContent = JSON.stringify(json, null, 2);
        if (json.url) {
          const img = document.getElementById('preview');
          img.src = json.url;
          img.style.display = 'block';
        }
      } catch (err) {
        document.getElementById('result').textContent = text;
      }
    }
  </script>
  </head>
  <body>
    <div class=\"card\">
      <h2>图片上传测试</h2>
      <form id=\"uploadForm\" onsubmit=\"handleSubmit(event)\">
        <label>文件</label>
        <input type=\"file\" name=\"file\" required />

        <label>标签（逗号分隔）</label>
        <input type=\"text\" name=\"tags\" placeholder=\"banner,home\" />

        <label>目标宽度</label>
        <input type=\"number\" name=\"width\" min=\"1\" />

        <label>目标高度</label>
        <input type=\"number\" name=\"height\" min=\"1\" />

        <label>目标格式</label>
        <select name=\"target_format\">
          <option value=\"\">(不指定)</option>
          <option value=\"png\">png</option>
          <option value=\"jpg\">jpg</option>
          <option value=\"webp\">webp</option>
        </select>

        <label>Bucket（可选）</label>
        <input type=\"text\" name=\"bucket\" placeholder=\"不填使用默认\" />

        <button type=\"submit\">上传</button>
      </form>
      <h3>响应</h3>
      <pre id=\"result\"></pre>
      <img id=\"preview\" alt=\"预览\" style=\"display:none; max-width: 100%; margin-top: 12px; border:1px solid #eee;\" />
    </div>
  </body>
</html>
    """


