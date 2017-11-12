"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""

# exif stripping
from django.core.files.uploadedfile import InMemoryUploadedFile
import io
from PIL import Image


def strip_img_metadata(in_memory_img):
    if not in_memory_img:
        return None
    content_type = ""
    if type(in_memory_img) == InMemoryUploadedFile:
        content_type = in_memory_img.content_type
    else:
        # XXX some testcases seem to create files with wrong file format. In case of erroneous magic
        #     bytes we do not strip any data.
        # TODO is there something we can do about that?
        pass

    # jpeg
    if content_type == "image/jpeg" or content_type == "image/jpg":
        img = Image.open(in_memory_img)
        img_io_bytes = io.BytesIO()
        img.save(img_io_bytes, format='JPEG')
        new_img = InMemoryUploadedFile(img_io_bytes, None, in_memory_img.name, 'image/jpeg',
                                       img_io_bytes.getbuffer().nbytes, None)
        new_img.seek(0)
        img.close()
        return new_img

    # TODO remove additional metadata for other formats
    return in_memory_img
