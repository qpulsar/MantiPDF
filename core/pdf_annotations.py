import fitz  # PyMuPDF
import json
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('pdf_annotations')

class PDFAnnotations:
    """Handles PDF annotations such as notes, highlights, etc."""

    def __init__(self, pdf_handler):
        """Initialize the PDF annotations handler.

        Args:
            pdf_handler: The PDFHandler instance containing the document.
        """
        self.pdf_handler = pdf_handler
        self.annotations = {}  # Dictionary to store annotations by page
        logger.debug("PDFAnnotations initialized")

    def add_note(self, page_index, rect, content, username=None):
        """Add a note annotation to the PDF.

        Args:
            page_index: The 0-based index of the page.
            rect: The rectangle (QRectF) where the note should be placed.
            content: The content of the note.
            username: The username of the note creator.

        Returns:
            The annotation object if successful, None otherwise.
        """
        logger.debug(f"Adding note at page {page_index}, rect: {rect}, content: {content}, username: {username}")
        
        if not self.pdf_handler.doc or not (0 <= page_index < self.pdf_handler.page_count):
            logger.error(f"Invalid document or page index: {page_index}")
            return None

        try:
            page = self.pdf_handler.doc[page_index]
            logger.debug(f"Got page {page_index}")
            
            # Create the annotation
            timestamp = datetime.now().strftime("%d.%m.%Y, %H:%M:%S")
            title = f"{username or 'Kullanıcı'} {timestamp}"
            
            # Log rect details for debugging
            logger.debug(f"Rect details - x: {rect.x()}, y: {rect.y()}, width: {rect.width()}, height: {rect.height()}")
            
            # Extract coordinates from the QRectF object
            try:
                # Create a fitz.Point from the coordinates
                point = fitz.Point(rect.x(), rect.y())
                logger.debug(f"Created fitz.Point: {point}")
                
                # Create a fitz.Rect from the QRectF
                fitz_rect = fitz.Rect(rect.x(), rect.y(), rect.x() + rect.width(), rect.y() + rect.height())
                logger.debug(f"Created fitz.Rect: {fitz_rect}")
            except Exception as e:
                logger.error(f"Error creating fitz objects from QRectF: {e}")
                return None
            
            # Create a text annotation
            try:
                annot = page.add_text_annot(point, content, title)
                logger.debug(f"Created text annotation: {annot}")
            except Exception as e:
                logger.error(f"Error creating text annotation: {e}")
                return None
            
            # Set visual properties for the annotation
            try:
                annot.set_colors(stroke=(1, 1, 0))  # Yellow border
                annot.set_border(width=1.0)  # Border width
                annot.update()
                logger.debug("Updated annotation properties")
            except Exception as e:
                logger.error(f"Error setting annotation properties: {e}")
            
            # Store the annotation in our dictionary
            try:
                if page_index not in self.annotations:
                    self.annotations[page_index] = []
                
                self.annotations[page_index].append({
                    "type": "note",
                    "rect": [rect.x(), rect.y(), rect.x() + rect.width(), rect.y() + rect.height()],
                    "content": content,
                    "title": title,
                    "creation_date": timestamp,
                    "username": username or "Kullanıcı"
                })
                logger.debug(f"Added annotation to dictionary for page {page_index}")
            except Exception as e:
                logger.error(f"Error storing annotation in dictionary: {e}")
            
            # Mark the document as modified
            self.pdf_handler.modified = True
            logger.debug("Document marked as modified")
            
            return annot
        except Exception as e:
            logger.error(f"Error adding note annotation: {e}")
            return None

    def add_circle_annotation(self, page_index, rect, content, username=None):
        """Add a circle annotation to the PDF.

        Args:
            page_index: The 0-based index of the page.
            rect: The rectangle (x0, y0, x1, y1) where the circle should be placed.
            content: The content of the circle.
            username: The username of the circle creator.

        Returns:
            The annotation object if successful, None otherwise.
        """
        logger.debug(f"Adding circle annotation at page {page_index}, rect: {rect}, content: {content}")
        
        if not self.pdf_handler.doc or not (0 <= page_index < self.pdf_handler.page_count):
            logger.error(f"Invalid document or page index: {page_index}")
            return None

        try:
            page = self.pdf_handler.doc[page_index]
            logger.debug(f"Got page {page_index}")
            
            # Create the annotation
            timestamp = datetime.now().strftime("%d.%m.%Y, %H:%M:%S")
            title = f"{username or 'Kullanıcı'} {timestamp}"
            
            # Log rect details for debugging
            logger.debug(f"Rect details - x: {rect.x()}, y: {rect.y()}, width: {rect.width()}, height: {rect.height()}")
            
            # Extract top-left point from the QRectF object
            try:
                point = fitz.Point(rect.x(), rect.y())  # Create a fitz.Point from the top-left coordinates
                logger.debug(f"Created top-left fitz.Point: {point}")
            except Exception as e:
                logger.error(f"Error creating fitz.Point from QRectF: {e}")
                return None
            
            # Calculate the center of the rectangle
            try:
                center_x = rect.x() + rect.width() / 2
                center_y = rect.y() + rect.height() / 2
                center_point = fitz.Point(center_x, center_y)
                logger.debug(f"Calculated center point: {center_point}")
            except Exception as e:
                logger.error(f"Error calculating center point: {e}")
                return None
            
            # Define the radius of the circle
            radius = 10  # Adjust as needed
            
            # Create a circle annotation
            try:
                annot = page.add_circle_annot(center_point, radius)
                logger.debug(f"Created circle annotation: {annot}")
            except Exception as e:
                logger.error(f"Error creating circle annotation: {e}")
                return None
            
            # Set the title using set_info method
            try:
                annot.set_info(title=title)
                logger.debug(f"Set annotation title: {title}")
            except Exception as e:
                logger.error(f"Error setting annotation title: {e}")
            
            # Set visual properties for the annotation
            try:
                annot.set_colors(stroke=(1, 1, 0))  # Yellow border
                annot.set_border(width=1.5)  # Border width
                logger.debug("Set annotation visual properties")
            except Exception as e:
                logger.error(f"Error setting annotation visual properties: {e}")
            
            # Create a line annotation to connect the circle to the point
            try:
                # Define start and end points for the line
                # Start point is the center of the circle
                start_point = center_point
                # End point is the original point
                end_point = point
                
                # Create a line annotation
                line_annot = page.add_line_annot(start_point, end_point)
                logger.debug(f"Created line annotation: {line_annot}")
                
                # Set line properties
                line_annot.set_colors(stroke=(1, 1, 0))  # Yellow line
                line_annot.set_border(width=1.0)  # Line width
                logger.debug("Set line annotation properties")
            except Exception as e:
                logger.error(f"Error creating or setting line annotation: {e}")
            
            # Update the annotations to apply changes
            try:
                annot.update()
                if 'line_annot' in locals():
                    line_annot.update()
                logger.debug("Updated annotations")
            except Exception as e:
                logger.error(f"Error updating annotations: {e}")
            
            # Store the annotation in our dictionary
            try:
                if page_index not in self.annotations:
                    self.annotations[page_index] = []
                
                self.annotations[page_index].append({
                    "type": "circle",
                    "rect": [rect.x(), rect.y(), rect.x() + rect.width(), rect.y() + rect.height()],
                    "content": content,
                    "title": title,
                    "creation_date": timestamp,
                    "username": username or "Kullanıcı",
                    "has_line": True  # Flag to indicate this circle has a connecting line
                })
                logger.debug(f"Added annotation to dictionary for page {page_index}")
            except Exception as e:
                logger.error(f"Error storing annotation in dictionary: {e}")
            
            # Mark the document as modified
            self.pdf_handler.modified = True
            logger.debug("Document marked as modified")
            
            return annot
        except Exception as e:
            logger.error(f"Error adding circle annotation: {e}")
            return None

    def get_annotations(self, page_index):
        """Get all annotations for a specific page.

        Args:
            page_index: The 0-based index of the page.

        Returns:
            A list of annotations for the page.
        """
        logger.debug(f"Getting annotations for page {page_index}")
        
        if not self.pdf_handler.doc or not (0 <= page_index < self.pdf_handler.page_count):
            logger.warning(f"Invalid document or page index: {page_index}")
            return []

        try:
            # Return annotations from our dictionary
            annotations = self.annotations.get(page_index, [])
            logger.debug(f"Found {len(annotations)} annotations for page {page_index}")
            return annotations
        except Exception as e:
            logger.error(f"Error getting annotations: {e}")
            return []

    def remove_annotation(self, page_index, annot_index):
        """Remove an annotation from the PDF.

        Args:
            page_index: The 0-based index of the page.
            annot_index: The index of the annotation to remove.

        Returns:
            True if successful, False otherwise.
        """
        if not self.pdf_handler.doc or not (0 <= page_index < self.pdf_handler.page_count):
            return False

        try:
            # Remove from our dictionary
            if page_index in self.annotations and 0 <= annot_index < len(self.annotations[page_index]):
                self.annotations[page_index].pop(annot_index)
                
                # Remove from the PDF document
                page = self.pdf_handler.doc[page_index]
                annots = list(page.annots())  # Convert generator to list
                if annots and 0 <= annot_index < len(annots):
                    page.delete_annot(annots[annot_index])
                    
                # Mark the document as modified
                self.pdf_handler.modified = True
                
                return True
            return False
        except Exception as e:
            print(f"Error removing annotation: {e}")
            return False

    def save_annotations(self, filepath):
        """Save annotations to a separate JSON file.

        Args:
            filepath: The path to save the annotations file.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Create the annotations directory if it doesn't exist
            annotations_dir = os.path.dirname(filepath)
            # Only create the directory if there are actual annotations to save
            if self.annotations and len(self.annotations) > 0:
                os.makedirs(annotations_dir, exist_ok=True)
                # Save the annotations to a JSON file
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self.annotations, f, ensure_ascii=False, indent=4)
                return True
            else:
                # If there are no annotations, do not create the folder or file
                return False
        except Exception as e:
            print(f"Error saving annotations: {e}")
            return False

    def load_annotations(self, filepath):
        """Load annotations from a separate JSON file.

        Args:
            filepath: The path to load the annotations file from.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Check if the annotations file exists
            if not os.path.exists(filepath):
                return False
                
            # Load the annotations from the JSON file
            with open(filepath, 'r', encoding='utf-8') as f:
                self.annotations = json.load(f)
                
            # Convert string keys to integers
            self.annotations = {int(k): v for k, v in self.annotations.items()}
                
            return True
        except Exception as e:
            print(f"Error loading annotations: {e}")
            return False
