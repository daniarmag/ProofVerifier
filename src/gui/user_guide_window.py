from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QLabel, QScrollArea, QWidget
from PyQt5.QtCore import Qt, QRect, QCoreApplication
from PyQt5.QtGui import QImage, QPixmap
import fitz

class UserGuideWindow(QMainWindow):
    def __init__(self, pdf_path=None):
        super().__init__()
        self.setWindowTitle("User Guide")
        self.setGeometry(100, 100, 800, 600)
        screen = QCoreApplication.instance().primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)
        self.content_widget = QWidget()
        self.scroll_area.setWidget(self.content_widget)
        self.content_layout = QVBoxLayout(self.content_widget)
        if pdf_path:
            self.load_pdf(pdf_path)

    def load_pdf(self, pdf_path):
        try:
            doc = fitz.open(pdf_path)  # Open the PDF
            for page_num in range(len(doc)):
                page = doc[page_num]
                pix = page.get_pixmap()
                qt_image = UserGuideWindow._convert_to_qimage(pix)
                label = QLabel()
                label.setPixmap(qt_image)
                label.setAlignment(Qt.AlignCenter)
                self.content_layout.addWidget(label, alignment=Qt.AlignCenter)
            doc.close()
        except Exception as e:
            print(f"Failed to load PDF: {e}")

    @staticmethod
    def _convert_to_qimage(pix):
        """
        Convert PyMuPDF pixmap to QImage.
        """
        img_format = QImage.Format_RGB888 if pix.alpha == 0 else QImage.Format_ARGB32
        qt_image = QImage(pix.samples, pix.width, pix.height, pix.stride, img_format)
        return QPixmap.fromImage(qt_image)
