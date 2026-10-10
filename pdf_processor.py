
import os
from pathlib import Path
os.environ["FLAGS_use_mkldnn"] = "0"
import pymupdf
from paddleocr import PaddleOCR
import traceback

def extract_pdf_text(pdf_path):
    document = pymupdf.open(pdf_path)


    try:
        ocr = PaddleOCR(
            lang="en",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            device="cpu",
            enable_mkldnn=False
        )
    except Exception:
        traceback.print_exc()
        raise

    pages = []

    for page_number, page in enumerate(document, start=1):

        page_content = []

        # Find tables on this page
        tables = page.find_tables()

        table_boxes = [
            table.bbox
            for table in tables.tables
        ]

        # Extract normal text blocks
        text_blocks = page.get_text("blocks")

        for block in text_blocks:
            x0, y0, x1, y1, text, *_ = block

            # Check whether this text block is inside a table
            inside_table = False

            for table_box in table_boxes:
                tx0, ty0, tx1, ty1 = table_box

                if (
                    x0 >= tx0
                    and y0 >= ty0
                    and x1 <= tx1
                    and y1 <= ty1
                ):
                    inside_table = True
                    break

            if not inside_table and text.strip():
                page_content.append(text.strip())

        # Add tables separately
        for table in tables.tables:

            rows = table.extract()

            for row in rows:
                row_text = " | ".join(
                    str(cell).strip() if cell is not None else ""
                    for cell in row
                )

                page_content.append(row_text)

        if page_content:

            pages.append(
                f"[Page {page_number}]\n"
                + "\n".join(page_content)
            )

        else:

            print(
                f"Page {page_number} has no extractable text. "
                "Running OCR..."
            )

            pixmap = page.get_pixmap(
                matrix=pymupdf.Matrix(2, 2)
            )

            image_path = f"ocr_page_{page_number}.png"

            pixmap = page.get_pixmap(
                matrix=pymupdf.Matrix(2, 2)
            )

            pixmap.save(image_path)

            result = ocr.predict(image_path)

            ocr_text = []

            for page_result in result:

                rec_texts = page_result["rec_texts"]

                for text in rec_texts:

                    if text and text.strip():
                        ocr_text.append(text.strip())

            Path(image_path).unlink(
                missing_ok=True
            )

            if ocr_text:

                pages.append(
                    f"[Page {page_number} - OCR]\n"
                    + "\n".join(ocr_text)
                )

            else:

                print(
                    f"OCR could not recognize text "
                    f"on page {page_number}."
                )
    document.close()

    return "\n\n".join(pages)


if __name__ == "__main__":

    pdf_path = "C:\\Users\\78794\\Downloads\\ocr_test_scanned.pdf"

    extracted_text = extract_pdf_text(pdf_path)

    print(extracted_text)


# python pdf_processor.py