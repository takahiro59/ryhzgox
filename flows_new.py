from PIL import Image
import io, gzip, time
import brotli

def measure(func):
    def _measure(*args, **kwargs):
        path = '/var/log/mitm.log'
        before = int(args[0].response.headers["content-length"])
        start = time.time()
        flow = func(args[0], **kwargs)
        end = time.time()
        after = int(flow.response.headers["content-length"])
        ct = args[0].response.headers["content-type"]
        ct = ct[0:10]
        with open(path, mode='a') as f:
            f.write(f'type:{ct}\tcompressed:{after / before :.2%}\treduced:{before - after}\tsource:{before}\ttime:{end - start:.5f}\n')
        return flow
    return _measure

def compress_gzip(flow):
    content_binay = io.BytesIO()
    gz = gzip.GzipFile(fileobj=content_binay, mode='w')
    gz.write(flow.response.content)
    gz.close()
    flow.response.content = content_binary.getvalue()
    flow.response.headers["content-encoding"] = "gzip"
    return flow

def compress_brotli(flow):
    flow.response.content = brotli.compress(flow.response.content, quality=10)
    flow.response.headers["content-encoding"] = "br"
    return flow

def compress_png(flow):
    img = Image.open(io.BytesIO(flow.response.content))
    if img.mode == "RGBA" or "transparency" in img.info:
        content_binary = io.BytesIO()
        img = img.convert(mode='P', palette=Image.ADAPTIVE)
        #img.save(content_binary, "png", optimize = True, bits = 8)
        img.save(content_binary, bits = 8)
        flow.response.content = content_binary.getvalue()
    else:
        flow = compress_jpeg(flow)
    return flow

def compress_jpeg(flow):
    content_binary = io.BytesIO()
    img = Image.open(io.BytesIO(flow.response.content)).convert("RGB")
    img.save(content_binary, "jpeg", quality = 5, optimize = True, progressive = True)
    flow.response.headers["content-type"] = "image/jpeg"
    flow.response.content = content_binary.getvalue()
    return flow

# @measure
def compress(flow):
    if "content-type" in flow.response.headers and "content-length" in flow.response.headers:
        ct = str(flow.response.headers["content-type"])
        cl = int(flow.response.headers["content-length"])
        if (cl) > 1024:
            if (ct) [0:6] == ("image/") and (ct) [0:9] != ("image/svg"):
                if (ct) [0:9] == ("image/png"):
                    flow = compress_png(flow)
                else:
                    flow = compress_jpeg(flow)
            elif flow.request.scheme == "http" and not "content-encoding" in flow.response.headers:
                flow.response.headers["content-encoding"] = "none"
                if (ct) [0:5] == ("text/") or (ct) [0:12] == ("application/") or (ct) [0:9] == ("image/svg"):
                    flow = compress_gzip(flow)
            elif flow.request.scheme == "https" and not "content-encoding" in flow.response.headers:
                flow.response.headers["content-encoding"] = "none"
                if (ct) [0:5] == ("text/") or (ct) [0:12] == ("application/") or (ct) [0:9] == ("image/svg"):
                    flow = compress_brotli(flow)
    return flow

def response(flow):
    flow = compress(flow)