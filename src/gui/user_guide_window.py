from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QLabel, QScrollArea, QWidget
from PyQt5.QtCore import Qt, QRect, QCoreApplication
from PyQt5.QtGui import QImage, QPixmap
import fitz

class UserGuideWindow(QMainWindow):
    """
    A window to display the user guide PDF.
    """
    def __init__(self, pdf_path=None):
        super().__init__()
        self.setWindowTitle("User Guide")
        self.setGeometry(100, 100, 800, 600)
        self.center_window()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)

        self.content_widget = QWidget()
        self.scroll_area.setWidget(self.content_widget)
        self.content_layout = QVBoxLayout(self.content_widget)

        if pdf_path:
            self.load_pdf(pdf_path)

    def center_window(self):
        """
        Centers the window on the screen.
        """
        screen_geometry = QCoreApplication.instance().primaryScreen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

    def load_pdf(self, pdf_path):
        """
        Loads the PDF file and displays its pages as images.
        Args:
            pdf_path (str): Path to the PDF file.
        """
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                pix = page.get_pixmap()
                qt_image = UserGuideWindow._convert_to_qimage(pix)
                self.add_page_to_layout(qt_image)
            doc.close()
        except Exception as e:
            error_label = QLabel(f"Failed to load PDF: {e}")
            error_label.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(error_label)

    def add_page_to_layout(self, qt_image):
        """
        Adds a rendered PDF page as a QLabel to the layout.
        Args:
            qt_image (QPixmap): Image of the rendered PDF page.
        """
        label = QLabel()
        label.setPixmap(qt_image)
        label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(label)

    @staticmethod
    def _convert_to_qimage(pix):
        """
        Converts a PyMuPDF pixmap to a QPixmap.
        Args:
            pix (fitz.Pixmap): The PyMuPDF pixmap object.
        Returns:
            QPixmap: The converted QPixmap object.
        """
        img_format = QImage.Format_RGB888 if pix.alpha == 0 else QImage.Format_ARGB32
        qt_image = QImage(pix.samples, pix.width, pix.height, pix.stride, img_format)
        return QPixmap.fromImage(qt_image)
