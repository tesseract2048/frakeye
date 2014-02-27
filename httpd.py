import tornado.web
import tornado.httpserver
import cv2
import frakeye
import zlib
import re
import os
import hashlib

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", IndexHandler),
            (r"/about", AboutHandler),
            (r"/static/(.*)", tornado.web.StaticFileHandler, {'path': 'static'}),
            (r"/frak-pic", FrakPicHandler),
            (r"/frak", FrakHandler)
        ]
        tornado.web.Application.__init__(self, handlers)

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("tpl/index.html")

class AboutHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("tpl/about.html")

class FrakHandler(tornado.web.RequestHandler):
    def post(self):
        colormod = self.get_argument('colormod')
        mods = {"vampire": frakeye.MOD_VAMPIRE, "hollow": frakeye.MOD_HOLLOW, "cataract": frakeye.MOD_CATARACT}
        imgfile = self.request.files['img'][0]
        body = imgfile['body']
        checksum = "%08x" % (zlib.adler32(body) & 0xffffffff)
        checksum =  hashlib.md5("%s%s" % (checksum, colormod)).hexdigest()
        uploadpath = "uploads/%s" % checksum
        output_file = open(uploadpath, 'w')
        output_file.write(body)
        output_file.close()
        img = cv2.imread(uploadpath)
        newimg, width, height, count = frakeye.process(img, mods[colormod])
        if width > 480:
            height = int(float(height) / float(width) * 480.0)
            width = 480
        if height > 360:
            width = int(float(width) / float(height) * 360.0)
            height = 360
        savepath = "pics/%s.png" % checksum
        cv2.imwrite(savepath, newimg)
        self.render("tpl/frak.html", checksum=checksum, width=width, height=height, count=count)

class FrakPicHandler(tornado.web.RequestHandler):
    def get(self):
        checksum = self.get_argument('x')
        if not re.match("[a-z0-9]{8}", checksum):
            raise tornado.web.HTTPError(404)
        filepath = "pics/%s.png" % checksum
        if not os.path.isfile(filepath):
            raise tornado.web.HTTPError(404)
        self.set_header('Content-Type', 'image/png')
        with open(filepath, 'rb') as f:
            data = f.read()
            self.write(data)
        self.finish()

def main():
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(8000)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()