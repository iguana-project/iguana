"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""

from django.core.exceptions import ValidationError
# exif stripping
from django.core.files.uploadedfile import InMemoryUploadedFile
import io
from PIL import Image
# file type verification
import magic
from common.settings import (ALLOWED_IMG_EXTENSIONS, MAX_IMG_SIZE_BASE, MAXIMUM_IMG_SIZE,
                             MAX_FILE_SIZE_BASE, MAXIMUM_FILE_SIZE)

from django.utils.translation import ugettext_lazy as _


def create_img(in_memory_img, format_str, suffix_str, content_type):
    # remove any possible suffixes to avoid possible confusion
    img_name = in_memory_img.name.partition(".")[0]
    img = Image.open(in_memory_img)
    img_io_bytes = io.BytesIO()
    # img.save(img_io_bytes, format=format_str)
    # new_img = InMemoryUploadedFile(img_io_bytes, None, img_name+suffix_str, content_type,
    #                                img_io_bytes.getbuffer().nbytes, None)
    # store the image always as jpeg
    # TODO I'm not sure yet whether this sanitizes the image too
    img.save(img_io_bytes, format="JPEG")
    new_img = InMemoryUploadedFile(img_io_bytes, None, img_name+".jpg", "image/jpeg",
                                   img_io_bytes.getbuffer().nbytes, None)
    new_img.seek(0)
    img.close()
    return new_img


# It is necessary to strip any meta informations before the image is stored for the first time. In many other
# approaches those informations are striped after the image has been stored. Hence a leak would be possible for a short
# amount of time. Therefore InMemory representation is used to prevent any leaks.
# \param in_memory_file the file that has been uploaded
# \param has_to_be_an_image bool that signalises if the file has been uploaded via the CustomImageField
#        or if it is a general attachment
def return_in_memory_file(in_memory_file, has_to_be_an_image):
    if not in_memory_file:
        return None

    # file size limitation
    if has_to_be_an_image:
        if in_memory_file.size > MAXIMUM_IMG_SIZE:
            raise ValidationError(_("The uploaded image exceeds the allowed file size of: ") +
                                  str(MAX_IMG_SIZE_BASE)+" MB", code='file_too_big')
    else:
        # it is possible to upload larger images as an attachment
        if in_memory_file.size > MAXIMUM_FILE_SIZE:
            raise ValidationError(_("The uploaded file exceeds the allowed file size of: ") +
                                  str(MAX_FILE_SIZE_BASE)+" MB", code='file_too_big')

    content_type = ""
    """
    if type(in_memory_file) == InMemoryUploadedFile:
        content_type = in_memory_file.content_type
    else:
        # XXX some testcases seem to create files with wrong file format. In case of erroneous magic
        #     bytes we do not strip any data.
        # TODO is there something we can do about that?
        pass
    """

    # "Like any data supplied by the user, you shouldn't trust that the uploaded file is actually this type.
    # You’ll still need to validate that the file contains the content that the content-type header claims -
    # “trust but verify.”"    therefore the actual type is checked
    # Normally chunks() is preferred over read(), since the later one has some DOS-potential because of the
    # huge memory usage for big files. But this should be fine since there is a file size limitation.
    img_type = magic.from_buffer(in_memory_file.read(in_memory_file.size))
    in_memory_file.seek(0)

    # bmp
    if "PC bitmap" in img_type:
        """
        if content_type != "image/bmp":
            raise ValidationError(_("There is a mismatch between the file header and content-type header"),
                                  code='img_type_missmatch')
        """
        return create_img(in_memory_file, "BMP", ".bmp", content_type)

    # jpe, jpeg, jpg
    if "JPEG image data" in img_type:
        """
        if content_type != "image/jpeg" and content_type != "image/jpg":
            raise ValidationError(_("There is a mismatch between the file header and content-type header"),
                                  code='img_type_missmatch')
        """
        return create_img(in_memory_file, "JPEG", ".jpg", content_type)

    # gif
    if "GIF image data" in img_type:
        """
        if content_type != "image/gif":
            raise ValidationError(_("There is a mismatch between the file header and content-type header"),
                                  code='img_type_missmatch')
        """
        return create_img(in_memory_file, "GIF", ".gif", content_type)
    # png
    if "PNG image data" in img_type:
        """
        if content_type != "image/png":
            raise ValidationError(_("There is a mismatch between the file header and content-type header"),
                                  code='img_type_missmatch')
        """
        return create_img(in_memory_file, "PNG", ".png", content_type)

    """
    # tif, tiff
    if content_type == "image/tiff":
        if "TIFF image data" not in img_type:
            raise ValidationError(_("There is a mismatch between the file header and content-type header"),
                                  code='img_type_missmatch')
        return create_img(in_memory_file, "TIFF", ".tiff", content_type)
    # pbm, pgm, ppm
    if "Netpbm image data" in img_type:
        return create_img(in_memory_file, "PPM", ".ppm", content_type)
    """

    # since svg is not a valid extension it can not be uploaded. Hence this image has to be the default-avatar
    if "VG Scalable Vector Graphics image" in img_type:
        return in_memory_file

    # The file has been uploaded as a general attachment
    # TODO This is not perfect yet, there are additional image file formats.
    #      Also this doesn't stop malicious code to be uploaded
    if not has_to_be_an_image:
        return in_memory_file

    # The file has been uploaded via the CustomImageField and no supported image matched the file type
    raise ValidationError(_("Either unable to detect the image type or the image type is not supported." +
                            "Supported image extensions are: ") + str(ALLOWED_IMG_EXTENSIONS), code='unknown_img_type')


def strip_if_file_is_an_img(in_memory_file):
    return return_in_memory_file(in_memory_file, False)


def strip_img_metadata(in_memory_img):
    return return_in_memory_file(in_memory_img, True)
