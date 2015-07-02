""" PhotoUpload class is for common functionality in uploading photos for the
10coupons site.
 """
import os
import StringIO

from django.core.files import File

from PIL import Image, ExifTags

class PhotoUpload():
    """ Assisting methods to help with file upload processes. """
    
    @staticmethod
    def open_image(temp_image):
        """ Open a this image using StringIO. """
        image_file  = StringIO.StringIO(temp_image.read())
        image = Image.open(image_file)
        return image
    
    @staticmethod
    def check_image_orientation(image):
        """ Digital photo devices attach EXIF data to an image when a photo
        is taken.  In order to display an image appropriately without it
        getting rotated, we need to check its EXIF-->Orientation and rotate
        the image back to level.  Rotation will be needed if a camera takes a
        picture as a Portrait or if the camera is rotated from the 0,0 reference
        position from the horizon.
        """
        try:
            for orientation in ExifTags.TAGS.keys() : 
                if ExifTags.TAGS[orientation] == 'Orientation':
                    exif = dict(image._getexif().items())      
                    if   exif[orientation] == 3 : 
                        image = image.rotate(180, expand=True)
                    elif exif[orientation] == 6 : 
                        image = image.rotate(270, expand=True)
                    elif exif[orientation] == 8 : 
                        image = image.rotate(90, expand=True)
                    break
        except (AttributeError, KeyError):
            pass
        return image

    @staticmethod
    def square_off_image(image):
        """ Crop off this images long sides.  This method will crop in the
        following manner:
        
        Landscape Photo --> Crop off the left and right side equally
        Portrait Photo --> Crop off the top and bottom equally
        Square Photo --> Will fall into the Portrait Photo code and will get
                           handled appropriately. 
        """
        (actual_width, actual_height) = image.size
        if actual_width > actual_height:
            # Landscape
            left_crop = (actual_width - actual_height)/2
            right_crop = actual_width - left_crop
            square_image = image.crop((left_crop, 0, right_crop, actual_height))
        else:
            # Portrait or Square Photo
            up_crop = (actual_height - actual_width)/2
            down_crop = actual_height - up_crop
            square_image = image.crop((0, up_crop, actual_width, down_crop))
        return square_image
    
    @staticmethod
    def convert_to_rgb(image):
        """ Convert this image to RGB mode if it is not already. This is
        necessary in the case of saving a gif file to a jpeg. jpeg's are RGB """
        if image.mode != "RGB":
            image = image.convert("RGB")
        return image
    
    @staticmethod    
    def resize_image(image, width=200, height=200):
        """ Method to resize this image and save it. """
        resized_image = image.resize((width, height), Image.ANTIALIAS)  
        image_file = StringIO.StringIO()
        resized_image.save(image_file,'JPEG')
        return resized_image

    @staticmethod
    def save_image(image, model_image_field, filename, file_type='JPEG'):
        """ Save to disk """
        image_file = open(os.path.join('/tmp', filename), 'w')
        image.save(image_file, file_type, quality=95)
        image_file = open(os.path.join('/tmp', filename), 'r')
        content = File(image_file)
        model_image_field.save(filename, content)
    
PHOTO_UPLOAD = PhotoUpload()