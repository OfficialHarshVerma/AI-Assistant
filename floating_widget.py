
import sys
from PySide6.QtWidgets import QStackedWidget
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtCore import Qt, QPoint, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QFileDialog,
)
from llama_manager import LlamaServerManager
from pathlib import Path
# Import the functions from your existing chatbot.
# main.py will not execute its terminal interface when imported.
from main import (
    process_input,
    create_chatbot,
    create_pdf_chatbot,
    convert_image_to_pdf
)

from pdf_processor import extract_pdf_text


# ==================================================
# BACKGROUND WORKER
# ==================================================

class ChatWorker(QThread):
    status_changed = Signal(str)
    video_loaded = Signal(object, str)
    answer_ready = Signal(str)
    error_occurred = Signal(str)

    def __init__(
        self,
        task,
        video_path=None,
        video_url=None,
        chain=None,
        question=None,
        chat_history=None
    ):
        super().__init__()

        self.task = task
        self.video_path = video_path
        self.video_url = video_url
        self.chain = chain
        self.question = question
        self.chat_history = chat_history or []

    def run(self):
        print("CHAT WORKER STARTED:", self.task)
        try:

            # -----------------------------
            # LOCAL VIDEO
            # -----------------------------
            if self.task == "load_video":

                self.status_changed.emit(
                    "Loading local video transcript... This may take a while."
                )

                transcript_segments, video_id = process_input(
                    self.video_path
                )

                self.status_changed.emit(
                    "Preparing chatbot... Loading embeddings, FAISS and language models."
                )

                main_chain = create_chatbot(
                    transcript_segments,
                    video_id
                )

                self.video_loaded.emit(
                    main_chain,
                    video_id
                )

            # -----------------------------
            # YOUTUBE VIDEO
            # -----------------------------
            elif self.task == "load_youtube":

                self.status_changed.emit(
                    "Loading YouTube transcript... This may take a while."
                )

                transcript_segments, video_id = process_input(
                    self.video_url
                )

                self.status_changed.emit(
                    "Preparing chatbot... Loading embeddings, FAISS and language models."
                )

                main_chain = create_chatbot(
                    transcript_segments,
                    video_id
                )

                self.video_loaded.emit(
                    main_chain,
                    video_id
                )

            # -----------------------------
            # PDF
            # -----------------------------
            elif self.task == "load_pdf":

                self.status_changed.emit(
                    "Loading PDF... This may take a while."
                )

                pdf_text = extract_pdf_text(
                    self.video_path
                )

                self.status_changed.emit(
                    "Preparing chatbot... Loading embeddings, FAISS and language model."
                )

                pdf_id = Path(
                    self.video_path
                ).stem

                main_chain = create_pdf_chatbot(
                    pdf_text,
                    pdf_id
                )

                self.video_loaded.emit(
                    main_chain,
                    pdf_id
                )
            # IMAGE
            elif self.task == "load_image":

                self.status_changed.emit(
                    "Processing image with OCR... This may take a while."
                )

                temporary_pdf = convert_image_to_pdf(
                    self.video_path
                )

                try:
                    self.status_changed.emit(
                        "Running OCR on image..."
                    )

                    image_text = extract_pdf_text(
                        temporary_pdf
                    )

                    self.status_changed.emit(
                        "Preparing chatbot... Loading embeddings, FAISS and language model."
                    )

                    image_id = Path(
                        self.video_path
                    ).stem

                    main_chain = create_pdf_chatbot(
                        image_text,
                        image_id
                    )

                    self.video_loaded.emit(
                        main_chain,
                        image_id
                    )

                finally:
                    Path(
                        temporary_pdf
                    ).unlink(
                        missing_ok=True
                    )
            # -----------------------------
            # ASK QUESTION
            # -----------------------------
            elif self.task == "ask_question":

                self.status_changed.emit(
                    "Searching transcript and web..."
                )

                result = self.chain.invoke({
                    "question": self.question,
                    "chat_history": self.chat_history
                })

                self.answer_ready.emit(
                    str(result)
                )

        except Exception as error:

            self.error_occurred.emit(
                f"{type(error).__name__}: {error}"
            )


# ==================================================
# CHAT POPUP
# ==================================================

class ChatPopup(QWidget):


    def __init__(self):

        super().__init__()

        self.selected_video_path = None
        self.main_chain = None
        self.video_id = None
        self.worker = None
        self.chat_history = []
        self.exit_button = QPushButton("Exit")
        self.exit_button.setFixedHeight(32)

        self.exit_button.clicked.connect(
            QApplication.quit
        )

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        self.home_size = (400, 440)
        self.chat_size = (430, 480)

        self.setFixedSize(*self.home_size)

        # ==================================================
        # GLOBAL STYLE
        # ==================================================

        self.setStyleSheet("""

            QWidget#panel {
                background: qlineargradient(
                    x1: 0, y1: 0,
                    x2: 1, y2: 1,
                    stop: 0 #102d3d,
                    stop: 0.45 #0b2230,
                    stop: 1 #071722
                );

                border: 1px solid #294657;
                border-radius: 20px;
            }

            QWidget#panel {
                background-color: #0b141d;
                border: 1px solid #243746;
                border-radius: 20px;
            }

            QLabel {
                background: transparent;
                border: none;
            }

            QLineEdit {
                background-color: #111f2b;
                border: 1px solid #294354;
                border-radius: 12px;
                padding: 11px 14px;
                color: #f4f7fb;
                selection-background-color: #22d3ee;
                min-height: 22px;
            }

            QLineEdit:focus {
                border: 1px solid #22d3ee;
            }

            QLineEdit::placeholder {
                color: #718393;
            }

            QPushButton {
                background-color: #122431;
                border: 1px solid #294354;
                border-radius: 11px;
                color: #e8f7fb;
                padding: 10px 14px;
            }

            QPushButton:hover {
                background-color: #183544;
                border: 1px solid #22d3ee;
            }

            QPushButton:pressed {
                background-color: #0f2b39;
            }

            QPushButton:disabled {
                background-color: #101820;
                color: #52616d;
                border: 1px solid #202d36;
            }

            QTextEdit {
                background-color: #09121a;
                border: 1px solid #203341;
                border-radius: 15px;
                padding: 12px;
                color: #e9f4f7;
                font-size: 13px;
            }

            QScrollBar:vertical {
                background: transparent;
                width: 7px;
            }

            QScrollBar::handle:vertical {
                background: #294354;
                border-radius: 3px;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # ==================================================
        # MAIN PANEL
        # ==================================================

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            2, 2, 2, 2
        )

        panel = QWidget()

        panel.setObjectName("panel")

        main_layout.addWidget(panel)

        panel_layout = QVBoxLayout(panel)

        panel_layout.setContentsMargins(
            22, 20, 22, 20
        )

        panel_layout.setSpacing(8)
        panel_layout.addWidget(self.exit_button)

        # ==================================================
        # PAGE SWITCHER
        # ==================================================

        self.pages = QStackedWidget()

        panel_layout.addWidget(
            self.pages
        )

        # ==================================================
        # SCREEN 1 — HOME
        # ==================================================

        self.home_page = QWidget()

        home_layout = QVBoxLayout(
            self.home_page
        )

        home_layout.setContentsMargins(
            4, 4, 4, 4
        )

        home_layout.setSpacing(8)

        # --------------------------------------------------
        # HEADER
        # --------------------------------------------------

        header = QHBoxLayout()
        header.setSpacing(8)

        # -----------------------------------------------
        # BRAIN ICON
        # -----------------------------------------------

        header_icon = QSvgWidget()

        header_icon.setFixedSize(
            34, 34
        )

        header_icon.setStyleSheet("""
            QSvgWidget {
                background: transparent;
                border: none;
            }
        """)

        header_icon.load(
            """
            <svg width="34" height="34"
                 viewBox="0 0 64 64"
                 xmlns="http://www.w3.org/2000/svg">

                <defs>

                    <linearGradient id="brainHeader"
                        x1="15%" y1="10%"
                        x2="85%" y2="90%">

                        <stop offset="0%"
                            stop-color="#67e8f9"/>

                        <stop offset="50%"
                            stop-color="#22d3ee"/>

                        <stop offset="100%"
                            stop-color="#0ea5e9"/>

                    </linearGradient>

                </defs>


                <!-- ================================= -->
                <!-- FILLED BRAIN                      -->
                <!-- ================================= -->

                <path
                    d="
                    M31 13

                    C27 10 22 10 19 14
                    C14 13 10 17 11 22
                    C7 25 8 31 12 34
                    C8 38 10 43 15 45
                    C14 49 18 53 22 52
                    C24 56 29 57 32 53

                    L32 15

                    C32 14 32 13 31 13

                    M33 13

                    C37 10 42 10 45 14
                    C50 13 54 17 53 22
                    C57 25 56 31 52 34
                    C56 38 54 43 49 45
                    C50 49 46 53 42 52
                    C40 56 35 57 32 53

                    L32 15

                    C32 14 32 13 33 13
                    "

                    fill="url(#brainHeader)"
                    fill-rule="evenodd"
                />


                <!-- ================================= -->
                <!-- BRAIN GROOVES                     -->
                <!-- ================================= -->

                <path
                    d="
                    M18 22
                    C22 20 25 23 24 27
                    C23 30 25 32 28 31

                    M16 36
                    C20 34 23 36 22 40

                    M46 22
                    C42 20 39 23 40 27
                    C41 30 39 32 36 31

                    M48 36
                    C44 34 41 36 42 40

                    M32 17
                    L32 50
                    "

                    fill="none"
                    stroke="#07526a"
                    stroke-width="2.5"
                    stroke-linecap="round"
                />


                <!-- Small highlight -->
                <path
                    d="
                    M22 15
                    C19 16 17 19 17 22
                    "

                    fill="none"
                    stroke="#cffafe"
                    stroke-width="1.5"
                    stroke-linecap="round"
                    opacity="0.75"
                />

            </svg>
            """.encode("utf-8")
        )

        header.addWidget(
            header_icon
        )


        # -----------------------------------------------
        # TITLE
        # -----------------------------------------------

        title = QLabel(
            "AI Assistant"
        )

        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 700;
                color: #f5fbff;
                background: transparent;
                border: none;
            }
        """)

        header.addWidget(
            title
        )

        header.addStretch()


        # -----------------------------------------------
        # CLOSE BUTTON
        # -----------------------------------------------

        close_home = QPushButton()

        close_home.setFixedSize(
            30, 30
        )

        close_home.setText("×")

        close_home.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #94a3ad;
                font-family: "Segoe UI";
                font-size: 30px;
                font-weight: 450;
                padding: 0px;
                margin: 0px;
            }

            QPushButton:hover {
                color: #ffffff;
                background: #1b2932;
                border-radius: 8px;
            }

            QPushButton:pressed {
                background: #22343f;
            }
        """)

        close_home.clicked.connect(
            self.hide
        )

        header.addWidget(
            close_home
        )


        # -----------------------------------------------
        # ADD HEADER TO HOME
        # -----------------------------------------------

        home_layout.addLayout(
            header
        )

        # --------------------------------------------------
        # DESCRIPTION
        # --------------------------------------------------

        welcome = QLabel(
            "How may I help you\n today?"
        )

        welcome.setStyleSheet("""
            font-size: 21px;
            font-weight: 600;
            line-height: 1.3;
            color: #edf8fa;
            padding-top: 8px;
            padding-bottom: 4px;
        """)

        home_layout.addWidget(
            welcome

        )

        # --------------------------------------------------
        # YOUTUBE URL INPUT
        # --------------------------------------------------

        youtube_container = QWidget()

        youtube_container.setFixedHeight(46)

        youtube_container.setStyleSheet("""
            QWidget {
                background: #111c24;
                border: 1px solid #263944;
                border-radius: 20px;
            }
        """)

        youtube_row = QHBoxLayout(
            youtube_container
        )

        youtube_row.setContentsMargins(
            12, 0, 4, 0
        )

        youtube_row.setSpacing(4)


        # --------------------------------------------------
        # URL INPUT
        # --------------------------------------------------

        self.url_input = QLineEdit()

        self.url_input.setPlaceholderText(
            "Paste the YouTube URL"
        )

        self.url_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                outline: none;
                color: #e8f7fb;
                font-size: 12px;
                padding: 0px;
            }

            QLineEdit::placeholder {
                color: #617783;
            }
        """)

        youtube_row.addWidget(
            self.url_input,
            1
        )


        # --------------------------------------------------
        # LOAD BUTTON
        # --------------------------------------------------

        self.youtube_button = QPushButton("➜")

        self.youtube_button.setFixedSize(
            38,
            38
        )

        self.youtube_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.youtube_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 19px;
                color: #22d3ee;
                font-size: 20px;
                font-weight: 500;
                padding: 0px;
            }

            QPushButton:hover {
                background: #1a303a;
                color: #67e8f9;
            }

            QPushButton:pressed {
                background: #203b46;
                color: #a5f3fc;
            }
        """)

        self.youtube_button.clicked.connect(
            self.load_youtube_video
        )

        youtube_row.addWidget(
            self.youtube_button
        )

        home_layout.addWidget(
            youtube_container
        )



        # --------------------------------------------------
        # OR
        # --------------------------------------------------

        separator = QLabel(
            "────────  OR  ────────"
        )

        separator.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        separator.setStyleSheet("""
            QLabel {
                color: #526975;
                font-size: 11px;
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)

        home_layout.addWidget(
            separator
        )



        # --------------------------------------------------
        # FILE BUTTON
        # --------------------------------------------------

        self.file_button = QPushButton(
            "📁   Choose a file"
        )

        self.file_button.setStyleSheet("""
            QPushButton {
                background-color: #10242e;
                border: 1px solid #285363;
                border-radius: 11px;
                padding: 12px;
                color: #e4faff;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #153542;
                border: 1px solid #22d3ee;
            }
        """)

        self.file_button.clicked.connect(
            self.choose_local_file
        )

        home_layout.addWidget(
            self.file_button
        )
        # --------------------------------------------------
        # SUPPORTED TYPES
        # --------------------------------------------------

        source_row = QHBoxLayout()

        source_row.setSpacing(
            10
        )

        source_row.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )


        # --------------------------------------------------
        # HELPER FOR SOURCE ICONS
        # --------------------------------------------------

        def create_source_icon(
            svg,
            size=18
        ):

            icon = QSvgWidget()

            icon.setFixedSize(
                size,
                size
            )

            icon.setStyleSheet("""
                QSvgWidget {
                    background: transparent;
                    border: none;
                }
            """)

            icon.load(
                svg.encode("utf-8")
            )

            return icon


        # --------------------------------------------------
        # YOUTUBE
        # --------------------------------------------------

        youtube_icon = create_source_icon("""
        <svg width="18" height="18"
             viewBox="0 0 24 24"
             xmlns="http://www.w3.org/2000/svg">

            <rect
                x="3"
                y="5"
                width="18"
                height="14"
                rx="4"
                fill="#ff4d4d"
            />

            <path
                d="M10 8.5 L16 12 L10 15.5 Z"
                fill="white"
            />

        </svg>
        """)

        youtube_text = QLabel(
            "YouTube"
        )

        youtube_text.setStyleSheet("""
            QLabel {
                color: #8da4b3;
                font-size: 11px;
                background: transparent;
                border: none;
            }
        """)

        youtube_item = QHBoxLayout()

        youtube_item.setSpacing(
            5
        )

        youtube_item.addWidget(
            youtube_icon
        )

        youtube_item.addWidget(
            youtube_text
        )


        # --------------------------------------------------
        # VIDEO
        # --------------------------------------------------

        video_icon = create_source_icon("""
        <svg width="18" height="18"
             viewBox="0 0 24 24"
             xmlns="http://www.w3.org/2000/svg">

            <rect
                x="3"
                y="6"
                width="12"
                height="12"
                rx="3"
                fill="none"
                stroke="#38bdf8"
                stroke-width="1.8"
            />

            <path
                d="M15 10 L21 7.5 V16.5 L15 14 Z"
                fill="none"
                stroke="#38bdf8"
                stroke-width="1.8"
                stroke-linejoin="round"
            />

        </svg>
        """)

        video_text = QLabel(
            "Video"
        )

        video_text.setStyleSheet("""
            QLabel {
                color: #8da4b3;
                font-size: 11px;
                background: transparent;
                border: none;
            }
        """)

        video_item = QHBoxLayout()

        video_item.setSpacing(
            5
        )

        video_item.addWidget(
            video_icon
        )

        video_item.addWidget(
            video_text
        )


        # --------------------------------------------------
        # PDF
        # --------------------------------------------------

        pdf_icon = create_source_icon("""
        <svg width="18" height="18"
             viewBox="0 0 24 24"
             xmlns="http://www.w3.org/2000/svg">

            <path
                d="M6 2 H14 L19 7 V21 H6 Z"
                fill="none"
                stroke="#f87171"
                stroke-width="1.7"
                stroke-linejoin="round"
            />

            <path
                d="M14 2 V7 H19"
                fill="none"
                stroke="#f87171"
                stroke-width="1.7"
            />

            <text
                x="8"
                y="16"
                font-size="5"
                font-family="Arial"
                font-weight="bold"
                fill="#f87171">
                PDF
            </text>

        </svg>
        """)

        pdf_text = QLabel(
            "PDF"
        )

        pdf_text.setStyleSheet("""
            QLabel {
                color: #8da4b3;
                font-size: 11px;
                background: transparent;
                border: none;
            }
        """)

        pdf_item = QHBoxLayout()

        pdf_item.setSpacing(
            5
        )

        pdf_item.addWidget(
            pdf_icon
        )

        pdf_item.addWidget(
            pdf_text
        )


        # --------------------------------------------------
        # IMAGE
        # --------------------------------------------------

        image_icon = create_source_icon("""
        <svg width="18" height="18"
             viewBox="0 0 24 24"
             xmlns="http://www.w3.org/2000/svg">

            <rect
                x="3"
                y="4"
                width="18"
                height="16"
                rx="3"
                fill="none"
                stroke="#4ade80"
                stroke-width="1.7"
            />

            <circle
                cx="8"
                cy="9"
                r="2"
                fill="#4ade80"
            />

            <path
                d="M5 17 L10 12 L13 15 L16 12 L19 17"
                fill="none"
                stroke="#4ade80"
                stroke-width="1.7"
                stroke-linecap="round"
                stroke-linejoin="round"
            />

        </svg>
        """)

        image_text = QLabel(
            "Image"
        )

        image_text.setStyleSheet("""
            QLabel {
                color: #8da4b3;
                font-size: 11px;
                background: transparent;
                border: none;
            }
        """)

        image_item = QHBoxLayout()

        image_item.setSpacing(
            5
        )

        image_item.addWidget(
            image_icon
        )

        image_item.addWidget(
            image_text
        )


        # --------------------------------------------------
        # ADD ALL SOURCE TYPES
        # --------------------------------------------------

        source_row.addLayout(
            youtube_item
        )

        source_row.addLayout(
            video_item
        )

        source_row.addLayout(
            pdf_item
        )

        source_row.addLayout(
            image_item
        )

        home_layout.addLayout(
            source_row
        )


        # --------------------------------------------------
        # STATUS
        # --------------------------------------------------

        self.status_label = QLabel()

        self.status_label.setWordWrap(
            True
        )

        self.status_label.setStyleSheet("""
            QLabel {
                color: #718793;
                font-size: 11px;
                padding-top: 5px;
                background: transparent;
                border: none;
            }
        """)

        # Keep status_label available for the
        # existing worker/status code, but do not
        # show it on the home screen.

        self.status_label.hide()


        # --------------------------------------------------
        # BOTTOM SPACING
        # --------------------------------------------------

        home_layout.addSpacing(
            8
        )

        self.pages.addWidget(
            self.home_page
        )

        # ==================================================
        # SCREEN 2 — CHAT
        # ==================================================

        self.chat_page = QWidget()

        self.chat_page.setObjectName(
            "chat_page"
        )

        chat_layout = QVBoxLayout(
            self.chat_page
        )

        chat_layout.setContentsMargins(
            4, 4, 4, 4
        )

        chat_layout.setSpacing(
            8
        )


        # ==================================================
        # CHAT HEADER
        # ==================================================

        chat_header = QHBoxLayout()

        chat_header.setSpacing(
            8
        )


        # --------------------------------------------------
        # BACK BUTTON
        # --------------------------------------------------

        self.back_button = QPushButton(
            "‹"
        )

        self.back_button.setFixedSize(
            34,
            34
        )

        self.back_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.back_button.setStyleSheet("""
            QPushButton {
                background: #102b38;
                border: 1px solid #285161;
                border-radius: 9px;
                color: #bdeff7;
                font-size: 22px;
                padding: 0px;
            }

            QPushButton:hover {
                background: #153744;
                border: 1px solid #22d3ee;
                color: #ffffff;
            }

            QPushButton:pressed {
                background: #1b4654;
            }
        """)

        self.back_button.clicked.connect(
            self.show_home_page
        )

        chat_header.addWidget(
            self.back_button
        )


        # --------------------------------------------------
        # BRAIN ICON
        # --------------------------------------------------

        chat_icon = QSvgWidget()

        chat_icon.setFixedSize(
            34,
            34
        )

        chat_icon.setStyleSheet("""
            QSvgWidget {
                background: transparent;
                border: none;
            }
        """)

        chat_icon.load(
            """
            <svg width="34" height="34"
                viewBox="0 0 64 64"
                xmlns="http://www.w3.org/2000/svg">

                <defs>

                    <linearGradient
                        id="chatBrain"
                        x1="10%"
                        y1="10%"
                        x2="90%"
                        y2="90%">

                        <stop
                            offset="0%"
                            stop-color="#67e8f9"/>

                        <stop
                            offset="50%"
                            stop-color="#22d3ee"/>

                        <stop
                            offset="100%"
                            stop-color="#0ea5e9"/>

                    </linearGradient>

                </defs>

                <path
                    d="
                    M31 13

                    C27 10 22 10 19 14
                    C14 13 10 17 11 22
                    C7 25 8 31 12 34
                    C8 38 10 43 15 45
                    C14 49 18 53 22 52
                    C24 56 29 57 32 53

                    L32 15

                    C32 14 32 13 31 13

                    M33 13

                    C37 10 42 10 45 14
                    C50 13 54 17 53 22
                    C57 25 56 31 52 34
                    C56 38 54 43 49 45
                    C50 49 46 53 42 52
                    C40 56 35 57 32 53

                    L32 15

                    C32 14 32 13 33 13
                    "

                    fill="url(#chatBrain)"
                    fill-rule="evenodd"
                />

                <path
                    d="
                    M18 22
                    C22 20 25 23 24 27
                    C23 30 25 32 28 31

                    M16 36
                    C20 34 23 36 22 40

                    M46 22
                    C42 20 39 23 40 27
                    C41 30 39 32 36 31

                    M48 36
                    C44 34 41 36 42 40

                    M32 17
                    L32 50
                    "

                    fill="none"
                    stroke="#07526a"
                    stroke-width="2.5"
                    stroke-linecap="round"
                />

            </svg>
            """.encode("utf-8")
        )

        chat_header.addWidget(
            chat_icon
        )


        # --------------------------------------------------
        # TITLE + STATUS
        # --------------------------------------------------

        title_status = QVBoxLayout()

        title_status.setSpacing(
            1
        )

        title_status.setContentsMargins(
            0, 0, 0, 0
        )


        chat_title = QLabel(
            "Video Assistant"
        )

        chat_title.setStyleSheet("""
            QLabel {
                color: #f3fbff;
                font-size: 16px;
                font-weight: 700;
                background: transparent;
                border: none;
            }
        """)

        title_status.addWidget(
            chat_title
        )


        self.chat_status_label = QLabel(
            "● Ready"
        )

        self.chat_status_label.setStyleSheet("""
            QLabel {
                color: #4ade80;
                font-size: 10px;
                font-weight: 500;
                background: transparent;
                border: none;
                padding: 0px;
            }
        """)

        title_status.addWidget(
            self.chat_status_label
        )

        chat_header.addLayout(
            title_status
        )

        chat_header.addStretch()


        # --------------------------------------------------
        # CLOSE BUTTON
        # --------------------------------------------------

        close_button = QPushButton(
            "×"
        )

        close_button.setFixedSize(
            30,
            30
        )

        close_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        close_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #718793;
                font-family: "Segoe UI";
                font-size: 22px;
                font-weight: 400;
                padding: 0px;
            }

            QPushButton:hover {
                color: #ffffff;
                background: #172c38;
                border-radius: 8px;
            }

            QPushButton:pressed {
                background: #203b47;
            }
        """)

        close_button.clicked.connect(
            self.hide
        )

        chat_header.addWidget(
            close_button
        )

        chat_layout.addLayout(
            chat_header
        )


        # ==================================================
        # CHAT AREA
        # ==================================================

        self.chat_area = QTextEdit()

        self.chat_area.setReadOnly(
            True
        )

        self.chat_area.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: none;
                border-radius: 0px;
                padding: 8px 4px;
                color: #e9f7fa;
                font-size: 13px;
            }

            QScrollBar:vertical {
                background: transparent;
                width: 5px;
                margin: 4px 0px;
            }

            QScrollBar::handle:vertical {
                background: #285161;
                border-radius: 3px;
                min-height: 25px;
            }

            QScrollBar::handle:vertical:hover {
                background: #347084;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        chat_layout.addWidget(
            self.chat_area,
            1
        )


        # ==================================================
        # MESSAGE INPUT
        # ==================================================

        input_row = QHBoxLayout()

        input_row.setSpacing(
            8
        )


        self.message_input = QLineEdit()

        self.message_input.setPlaceholderText(
            "Ask a question..."
        )

        self.message_input.setFixedHeight(
            48
        )

        self.message_input.setStyleSheet("""
            QLineEdit {
                background: #102432;
                border: 1px solid #294858;
                border-radius: 15px;
                padding-left: 16px;
                padding-right: 14px;
                color: #eefcff;
                font-size: 12px;
            }

            QLineEdit:focus {
                border: 1px solid #22d3ee;
                background: #122a39;
            }

            QLineEdit::placeholder {
                color: #718b99;
            }
        """)

        self.message_input.returnPressed.connect(
            self.ask_question
        )

        input_row.addWidget(
            self.message_input,
            1
        )


        # --------------------------------------------------
        # SEND BUTTON
        # --------------------------------------------------

        self.send_button = QPushButton(
            "➤"
        )

        self.send_button.setFixedSize(
            52,
            52
        )

        self.send_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.send_button.setStyleSheet("""
            QPushButton {
                background: #19a9c2;
                border: none;
                border-radius: 26px;
                color: white;
                font-size: 20px;
                font-weight: 600;
                padding: 0px;
            }

            QPushButton:hover {
                background: #22c5df;
            }

            QPushButton:pressed {
                background: #118da5;
            }

            QPushButton:disabled {
                background: #28505d;
                color: #78929b;
            }
        """)

        self.send_button.clicked.connect(
            self.ask_question
        )

        input_row.addWidget(
            self.send_button
        )

        chat_layout.addLayout(
            input_row
        )


        # ==================================================
        # ADD CHAT PAGE
        # ==================================================

        self.pages.addWidget(
            self.chat_page
        )

        # ==================================================
        # START ON HOME PAGE
        # ==================================================

        self.pages.setCurrentWidget(
            self.home_page
        )

    def show_home_page(self):
        if self.worker is not None and self.worker.isRunning():
            return

        self.pages.setCurrentWidget(self.home_page)
        self.resize(*self.home_size)
        self.setFixedSize(*self.home_size)

        self.status_label.setText("Ready to load a video.")


    def load_youtube_video(self):
        video_url = self.url_input.text().strip()

        if not video_url:
            self.status_label.setText("Please paste a YouTube URL.")
            return

        if self.worker is not None and self.worker.isRunning():
            self.status_label.setText(
                "Please wait for the current task to finish."
            )
            return

        self.main_chain = None
        self.video_id = None
        self.selected_video_path = None

        self.chat_area.clear()
        self.chat_area.setPlainText(
            "Preparing your YouTube video...\n"
            "Transcript extraction will run in the background."
        )

        # Switch to the chat screen.
        self.pages.setCurrentWidget(self.chat_page)
        self.setFixedSize(*self.chat_size)
        self.chat_status_label.setText(
            "Loading YouTube transcript..."
        )

        # Disable buttons while the video is loading.
        self.youtube_button.setEnabled(False)
        self.file_button.setEnabled(False)
        self.send_button.setEnabled(False)

        self.worker = ChatWorker(
            task="load_youtube",
            video_url=video_url
        )

        self.worker.status_changed.connect(
            self.chat_status_label.setText
        )
        self.worker.video_loaded.connect(self.on_video_loaded)
        self.worker.error_occurred.connect(self.on_error)

        self.worker.start()

    # ----------------------------------------------
    # SELECT A LOCAL FILE
    # ----------------------------------------------

    def choose_local_file(self):

        if self.worker is not None and self.worker.isRunning():
            self.status_label.setText(
                "Please wait for the current task to finish."
            )
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose a Local File",
            "",
            "Supported Files (*.mp4 *.mkv *.avi *.mov *.webm *.flv *.pdf *.png *.jpg *.jpeg *.bmp *.webp)"
        )

        if not file_path:
            return

        # Check what type of file the user selected.
        suffix = Path(file_path).suffix.lower()
        print("SELECTED FILE:", file_path)
        print("FILE SUFFIX:", suffix)

        self.selected_video_path = file_path
        self.main_chain = None
        self.video_id = None

        self.chat_area.clear()

        # -----------------------------
        # PDF
        # -----------------------------

        if suffix == ".pdf":

            self.chat_area.setPlainText(
                "Preparing your PDF...\n"
                "PDF processing will run in the background."
            )

            self.pages.setCurrentWidget(self.chat_page)
            self.setFixedSize(*self.chat_size)

            self.chat_status_label.setText(
                "Loading PDF..."
            )

            self.file_button.setEnabled(False)
            self.youtube_button.setEnabled(False)
            self.send_button.setEnabled(False)

            self.worker = ChatWorker(
                task="load_pdf",
                video_path=file_path
            )

        # -----------------------------
        # IMAGE
        # -----------------------------

        elif suffix in (
            ".png",
            ".jpg",
            ".jpeg",
            ".bmp",
            ".webp"
        ):

            self.chat_area.setPlainText(
                "Preparing your image...\n"
                "OCR processing will run in the background."
            )

            self.pages.setCurrentWidget(self.chat_page)
            self.setFixedSize(*self.chat_size)

            self.chat_status_label.setText(
                "Processing image with OCR..."
            )

            self.file_button.setEnabled(False)
            self.youtube_button.setEnabled(False)
            self.send_button.setEnabled(False)

            self.worker = ChatWorker(
                task="load_image",
                video_path=file_path
            )

        # -----------------------------
        # LOCAL VIDEO
        # -----------------------------

        elif suffix in (
            ".mp4",
            ".mkv",
            ".avi",
            ".mov",
            ".webm",
            ".flv"
        ):

            self.chat_area.setPlainText(
                "Preparing your local video...\n"
                "Transcript extraction will run in the background."
            )

            self.pages.setCurrentWidget(self.chat_page)
            self.setFixedSize(*self.chat_size)

            self.chat_status_label.setText(
                "Loading local video transcript..."
            )

            self.file_button.setEnabled(False)
            self.youtube_button.setEnabled(False)
            self.send_button.setEnabled(False)

            self.worker = ChatWorker(
                task="load_video",
                video_path=file_path
            )

        else:

            self.chat_area.setPlainText(
                "Unsupported file type."
            )

            return

        # Connect worker signals.

        self.worker.status_changed.connect(
            self.chat_status_label.setText
        )

        self.worker.video_loaded.connect(
            self.on_video_loaded
        )

        self.worker.error_occurred.connect(
            self.on_error
        )

        print("STARTING WORKER:", self.worker.task)

        self.worker.start()

    # ----------------------------------------------
    # VIDEO / PDF LOADED
    # ----------------------------------------------

    def on_video_loaded(self, main_chain, source_id):

        self.main_chain = main_chain
        self.video_id = source_id

        if self.selected_video_path:
            file_name = Path(
                self.selected_video_path
            ).name
        else:
            file_name = "YouTube Video"

        self.chat_area.setPlainText(
            f"Loaded: {file_name}\n\n"
            "Ready! You can now ask questions.\n"
            "Answers will include document and web results."
        )

        self.chat_status_label.setText(
            "Ready"
        )

        self.file_button.setEnabled(True)
        self.youtube_button.setEnabled(True)
        self.send_button.setEnabled(True)

        self.file_button.setText(
            "Choose Another File"
        )

    # ----------------------------------------------
    # ASK A QUESTION
    # ----------------------------------------------

    def ask_question(self):

        question = self.message_input.text().strip()

        if not question:
            return

        if self.main_chain is None:
            self.chat_area.append(
                "Please load a video or PDF first."
            )
            return

        self.current_question = question

        self.message_input.clear()

        self.chat_area.append(
            f"\nYou: {question}\n"
        )

        self.chat_status_label.setText(
            "Searching..."
        )

        self.send_button.setEnabled(False)

        self.worker = ChatWorker(
            task="ask_question",
            chain=self.main_chain,
            question=question,
            chat_history=self.chat_history
        )

        self.worker.status_changed.connect(
            self.chat_status_label.setText
        )

        self.worker.answer_ready.connect(
            self.on_answer_ready
        )

        self.worker.error_occurred.connect(
            self.on_error
        )

        self.worker.finished.connect(
            lambda: self.send_button.setEnabled(True)
        )

        self.worker.start()
    # ----------------------------------------------
    # DISPLAY THE ANSWER
    # ----------------------------------------------

    def on_answer_ready(self, answer):

        self.chat_area.append(
            f"\nAssistant:\n{answer}\n"
        )

        self.chat_history.append(
            f"User: {self.current_question}\n"
            f"Assistant: {answer}"
        )
        print("CHAT HISTORY:", self.chat_history)
        self.chat_status_label.setText("Ready to chat.")

        self.send_button.setEnabled(True)
        self.file_button.setEnabled(True)
        self.youtube_button.setEnabled(True)

    # ----------------------------------------------
    # STATUS AND ERRORS
    # ----------------------------------------------

    def update_status(self, message):
        self.status_label.setText(message)

    def on_error(self, message):
        self.chat_status_label.setText("Something went wrong.")

        self.chat_area.append(
            f"\nError:\n{message}\n"
        )

        self.send_button.setEnabled(True)
        self.file_button.setEnabled(True)
        self.youtube_button.setEnabled(True)


# ==================================================
# FLOATING AI CIRCLE
# ==================================================

# ==================================================
# FLOATING AI BRAIN BUTTON
# ==================================================

class FloatingButton(QWidget):

    def __init__(self, popup):
        super().__init__()

        self.popup = popup
        self.drag_offset = QPoint()
        self.press_position = QPoint()
        self.dragged = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        # -----------------------------------------
        # BUTTON SIZE
        # -----------------------------------------

        self.setFixedSize(64, 64)

        # The SVG itself creates the complete circle.
        # Do NOT give the QWidget a square background.
        self.setStyleSheet("""
            QWidget {
                background: transparent;
                border: none;
            }
        """)
        # -----------------------------------------
        # AI BRAIN ICON
        # -----------------------------------------

        brain_svg = """
        <svg width="64" height="64"
             viewBox="0 0 64 64"
             xmlns="http://www.w3.org/2000/svg">

            <defs>

                <!-- Main dark glass surface -->
                <radialGradient id="surface"
                    cx="35%" cy="25%"
                    r="80%">

                    <stop offset="0%"
                        stop-color="#20394a"/>

                    <stop offset="45%"
                        stop-color="#102431"/>

                    <stop offset="100%"
                        stop-color="#07141e"/>
                </radialGradient>

                <!-- Cyan rim -->
                <linearGradient id="rim"
                    x1="15%" y1="10%"
                    x2="85%" y2="90%">

                    <stop offset="0%"
                        stop-color="#67e8f9"/>

                    <stop offset="45%"
                        stop-color="#22d3ee"/>

                    <stop offset="75%"
                        stop-color="#0ea5e9"/>

                    <stop offset="100%"
                        stop-color="#38bdf8"/>
                </linearGradient>

                <!-- Brain -->
                <linearGradient id="brain"
                    x1="20%" y1="10%"
                    x2="80%" y2="90%">

                    <stop offset="0%"
                        stop-color="#a5f3fc"/>

                    <stop offset="45%"
                        stop-color="#22d3ee"/>

                    <stop offset="100%"
                        stop-color="#38bdf8"/>
                </linearGradient>

                <!-- Top glass highlight -->
                <linearGradient id="highlight"
                    x1="0%" y1="0%"
                    x2="0%" y2="100%">

                    <stop offset="0%"
                        stop-color="#ffffff"
                        stop-opacity="0.20"/>

                    <stop offset="45%"
                        stop-color="#ffffff"
                        stop-opacity="0.04"/>

                    <stop offset="100%"
                        stop-color="#ffffff"
                        stop-opacity="0"/>
                </linearGradient>

            </defs>


            <!-- ================================= -->
            <!-- SOFT CYAN GLOW                    -->
            <!-- ================================= -->

            <circle
                cx="32"
                cy="32"
                r="31"
                fill="#22d3ee"
                opacity="0.06"
            />

            <circle
                cx="32"
                cy="32"
                r="30"
                fill="none"
                stroke="#22d3ee"
                stroke-width="3"
                opacity="0.10"
            />

            <circle
                cx="32"
                cy="32"
                r="29"
                fill="none"
                stroke="#22d3ee"
                stroke-width="2"
                opacity="0.16"
            />


            <!-- ================================= -->
            <!-- MAIN CIRCULAR BODY                -->
            <!-- ================================= -->

            <circle
                cx="32"
                cy="32"
                r="27"
                fill="url(#surface)"
            />


            <!-- ================================= -->
            <!-- OUTER 3D RIM                      -->
            <!-- ================================= -->

            <circle
                cx="32"
                cy="32"
                r="27"
                fill="none"
                stroke="#07131c"
                stroke-width="2"
            />

            <circle
                cx="32"
                cy="32"
                r="26"
                fill="none"
                stroke="url(#rim)"
                stroke-width="2"
            />

            <!-- Inner rim -->
            <circle
                cx="32"
                cy="32"
                r="24"
                fill="none"
                stroke="#38bdf8"
                stroke-width="0.7"
                opacity="0.45"
            />


            <!-- ================================= -->
            <!-- GLASS HIGHLIGHT                    -->
            <!-- ================================= -->

            <path
                d="
                M12 29
                C14 17 23 9 32 8
                C43 9 51 17 53 27
                C44 21 28 18 12 29
                Z
                "
                fill="url(#highlight)"
                opacity="0.55"
            />


            <!-- ================================= -->
            <!-- BRAIN                              -->
            <!-- ================================= -->

            <g transform="translate(6, 6) scale(0.81)">

                <!-- Left hemisphere -->
                <path
                    d="
                    M31 19
                    C28 15 23 15 21 19
                    C17 18 14 21 15 25
                    C11 27 12 32 15 34
                    C12 38 15 42 19 42
                    C18 46 22 49 26 47
                    C28 51 31 50 32 47
                    L32 21
                    C32 20 32 19 31 19
                    "
                    fill="none"
                    stroke="url(#brain)"
                    stroke-width="2.2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                />

                <!-- Right hemisphere -->
                <path
                    d="
                    M33 19
                    C36 15 41 15 43 19
                    C47 18 50 21 49 25
                    C53 27 52 32 49 34
                    C52 38 49 42 45 42
                    C46 46 42 49 38 47
                    C36 51 33 50 32 47
                    L32 21
                    C32 20 32 19 33 19
                    "
                    fill="none"
                    stroke="url(#brain)"
                    stroke-width="2.2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                />

                <!-- Brain folds -->
                <path
                    d="
                    M20 25
                    C23 23 26 25 25 28
                    C24 30 25 32 28 31
                    M19 37
                    C22 35 25 37 24 40
                    M44 25
                    C41 23 38 25 39 28
                    C40 30 39 32 36 31
                    M45 37
                    C42 35 39 37 40 40
                    M32 21
                    L32 47
                    "
                    fill="none"
                    stroke="#67e8f9"
                    stroke-width="1.7"
                    stroke-linecap="round"
                    opacity="0.95"
                />

                <!-- Small central highlight -->
                <path
                    d="M32 20 L32 46"
                    stroke="#cffafe"
                    stroke-width="0.7"
                    opacity="0.65"
                    stroke-linecap="round"
                />

            </g>

        </svg>
        """

        # -----------------------------------------
        # SVG WIDGET
        # -----------------------------------------

        self.brain_icon = QSvgWidget(self)

        self.brain_icon.setGeometry(
            0, 0, 64, 64
        )

        self.brain_icon.load(
            brain_svg.encode("utf-8")
        )

        self.brain_icon.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )

    # =============================================
    # DRAGGING
    # =============================================

    def mousePressEvent(self, event):

        if event.button() == Qt.MouseButton.LeftButton:

            self.press_position = (
                event.globalPosition().toPoint()
            )

            self.drag_offset = (
                self.press_position
                - self.frameGeometry().topLeft()
            )

            self.dragged = False

    def mouseMoveEvent(self, event):

        if event.buttons() & Qt.MouseButton.LeftButton:

            current_position = (
                event.globalPosition().toPoint()
            )

            if (
                current_position - self.press_position
            ).manhattanLength() > QApplication.startDragDistance():

                self.dragged = True

            if self.dragged:

                self.move(
                    current_position - self.drag_offset
                )

                if self.popup.isVisible():
                    self.position_popup()

    def mouseReleaseEvent(self, event):

        if event.button() == Qt.MouseButton.LeftButton:

            if not self.dragged:
                self.toggle_popup()

    # =============================================
    # POPUP
    # =============================================

    def toggle_popup(self):

        if self.popup.isVisible():

            self.popup.hide()

        else:

            self.position_popup()
            self.popup.show()
            self.popup.raise_()

    def position_popup(self):

        circle = self.frameGeometry()

        popup_width = self.popup.width()
        popup_height = self.popup.height()

        screen = QApplication.screenAt(
            circle.center()
        )

        if screen is None:
            screen = QApplication.primaryScreen()

        bounds = screen.availableGeometry()

        space_right = (
            bounds.right() - circle.right()
        )

        space_left = (
            circle.left() - bounds.left()
        )

        if (
            space_right >= popup_width
            or space_right >= space_left
        ):

            x = circle.right() + 10

        else:

            x = (
                circle.left()
                - popup_width
                - 10
            )

        y = circle.top()

        y = max(bounds.top(), y)

        y = min(
            y,
            bounds.bottom()
            - popup_height
            + 1
        )

        x = max(bounds.left(), x)

        x = min(
            x,
            bounds.right()
            - popup_width
            + 1
        )

        self.popup.move(x, y)

# ==================================================
# START APPLICATION
# ==================================================

if __name__ == "__main__":

    app = QApplication(sys.argv)

    llama_server = LlamaServerManager()

    try:
        llama_server.start()

    except Exception as e:
        print("Failed to start Qwen server:")
        print(e)
        sys.exit(1)

    popup = ChatPopup()
    floating_button = FloatingButton(popup)

    screen = app.primaryScreen().availableGeometry()

    floating_button.move(
        screen.right() - floating_button.width() - 30,
        screen.top() + 80,
    )

    floating_button.show()

    print("Floating AI assistant is running.")

    app.aboutToQuit.connect(
        llama_server.stop
    )

    sys.exit(app.exec())
# python floating_widget.py