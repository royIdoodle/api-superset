import aiohttp
import mimetypes
from typing import Optional
from urllib.parse import urlparse, unquote

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..oss import upload_bytes, suggest_object_key
from ..schemas import PdfTransferRequest, PdfTransferResponse

router = APIRouter()


def _get_filename_from_url(url: str) -> str:
    """从URL中提取文件名"""
    parsed_url = urlparse(url)
    path = unquote(parsed_url.path)
    filename = path.split('/')[-1]
    if not filename:
        # 如果URL路径以/结尾，没有文件名，使用默认名称
        filename = "document.pdf"
    return filename


@router.post("/transfer", response_model=PdfTransferResponse, status_code=status.HTTP_201_CREATED)
async def transfer_pdf(
    *, 
    request: PdfTransferRequest,
    db: Session = Depends(get_db),
):
    url = request.url
    bucket = request.bucket
    """转存在线PDF文件到OSS
    
    参数:
    - url: 在线PDF文件的URL
    - bucket: 可选，目标OSS bucket
    
    返回:
    - bucket: 存储的bucket名称
    - key: OSS中的对象key
    - url: 可访问的公共URL
    """
    # 验证URL格式
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        raise HTTPException(status_code=400, detail="无效的URL格式")

    # 下载在线PDF文件
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"无法下载文件，HTTP状态码: {response.status}"
                    )
                
                # 检查Content-Type
                content_type = response.headers.get("Content-Type", "")
                if not content_type.startswith("application/pdf"):
                    # 即使Content-Type不是PDF，也尝试检查文件内容
                    # 有些服务器可能不会正确设置Content-Type
                    pass

                # 读取文件内容
                pdf_data = await response.read()
                if not pdf_data:
                    raise HTTPException(status_code=400, detail="下载的文件为空")
                
                # 检查文件内容是否为PDF
                if not pdf_data.startswith(b"%PDF-"):
                    raise HTTPException(status_code=400, detail="文件内容不是PDF格式")
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=400, detail=f"下载文件失败: {str(e)}")

    # 从URL提取文件名
    original_filename = _get_filename_from_url(url)
    
    # 上传到OSS
    content_type = mimetypes.guess_type(original_filename)[0] or "application/pdf"
    try:
        final_bucket, final_key, public_url = upload_bytes(
            pdf_data,
            original_filename=original_filename,
            bucket_name=bucket,
            content_type=content_type,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传文件失败: {str(e)}")

    return PdfTransferResponse(
        bucket=final_bucket,
        key=final_key,
        url=public_url
    )


@router.get("/transfer/test", response_class=HTMLResponse)
def transfer_test_page() -> str:
    """PDF转存测试页面"""
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>PDF转存测试</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif; padding: 24px; }
    .card { max-width: 720px; margin: 0 auto; border: 1px solid #ddd; border-radius: 8px; padding: 20px; }
    label { display: block; margin-top: 12px; font-weight: 600; }
    input { width: 100%; padding: 8px; margin-top: 6px; }
    button { margin-top: 16px; padding: 10px 16px; font-weight: 600; }
    pre { background: #f7f7f7; padding: 12px; white-space: pre-wrap; word-break: break-all; }
    .success { color: #1890ff; }
    .error { color: #f5222d; }
  </style>
  <script>
    async function handleSubmit(e) {
      e.preventDefault();
      const urlInput = document.getElementById('pdfUrl');
      const bucketInput = document.getElementById('bucket');
      const resultDiv = document.getElementById('result');
      const downloadLink = document.getElementById('downloadLink');
      
      resultDiv.textContent = '转存中...';
      downloadLink.style.display = 'none';
      
      try {
        const resp = await fetch('/pdfs/transfer', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            url: urlInput.value,
            bucket: bucketInput.value || undefined
          })
        });
        
        const data = await resp.json();
        
        if (resp.ok) {
          resultDiv.className = 'success';
          resultDiv.textContent = JSON.stringify(data, null, 2);
          if (data.url) {
            downloadLink.href = data.url;
            downloadLink.textContent = '点击下载转存后的PDF';
            downloadLink.style.display = 'block';
          }
        } else {
          resultDiv.className = 'error';
          resultDiv.textContent = `转存失败: ${JSON.stringify(data, null, 2)}`;
        }
      } catch (err) {
        resultDiv.className = 'error';
        resultDiv.textContent = `转存失败: ${err.message}`;
      }
    }
    
    // 填充示例URL
    function fillExample(url) {
      document.getElementById('pdfUrl').value = url;
    }
  </script>
  </head>
  <body>
    <div class="card">
      <h2>PDF转存测试</h2>
      <form id="transferForm" onsubmit="handleSubmit(event)">
        <label>在线PDF URL</label>
        <input 
          type="text" 
          id="pdfUrl" 
          name="url" 
          required 
          placeholder="https://example.com/document.pdf"
          style="font-family: monospace;"
        />
        
        <div style="margin-top: 8px;">
          <button type="button" onclick="fillExample('https://arxiv.org/pdf/2505.20411')">使用示例1</button>
          <button type="button" onclick="fillExample('https://dnu-cdn.xpertiise.com/wangchong/db8a1a24-f5cd-4155-8f76-ffa63c4a2a43.pdf')">使用示例2</button>
        </div>

        <label>Bucket（可选）</label>
        <input type="text" id="bucket" name="bucket" placeholder="不填使用默认" />

        <button type="submit">开始转存</button>
      </form>
      
      <h3>转存结果</h3>
      <pre id="result"></pre>
      
      <a id="downloadLink" style="display: none; margin-top: 12px;" target="_blank">点击下载转存后的PDF</a>
    </div>
  </body>
</html>
    """