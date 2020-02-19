"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
import io
import os
import re
from libxmp import XMPFiles, consts, XMPMeta
import piexif
from PIL import Image, ImageDraw, PngImagePlugin
from shutil import copyfile, rmtree

from django.test import TestCase
from django.urls.base import reverse

from project.models import Project
from issue.models import Issue
from django.contrib.auth import get_user_model
from common.settings import ALLOWED_IMG_EXTENSIONS, MEDIA_ROOT, TEST_FILE_PATH


user_name = 'a'
user_email = 'b@b.com'
timezone = "Europe/Berlin"
avatars_path = os.path.join(MEDIA_ROOT, "avatars", user_name)
forbidden_img = 'forbidden_img.tiff'


class StripImgMetadataTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user(user_name, user_email, 'c')
        cls.project = Project(creator=cls.user, name_short='PRJ')
        cls.project.save()
        cls.project.manager.add(cls.user)
        cls.project.developer.add(cls.user)
        cls.images = list(cls.create_images())
        # TODO https://blog.brian.jp/python/png/2016/07/07/file-fun-with-pyhon.html
        # TODO malicious payload jpg, png, bmp, gif

    @classmethod
    def tearDownClass(cls):
        for image in cls.images:
            os.unlink(image)
        os.unlink(forbidden_img)
        super().tearDownClass()

    def setUp(self):
        self.client.force_login(self.user)
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()
        self.issue = Issue(title="Test-Issue", project=self.project)
        self.issue.save()

    def tearDown(self):
        # delete uploaded avatars
        rmtree(avatars_path, ignore_errors=True)
        # TODO TESTCASE delete all uploaded files (the files that are stored on server side
        #               so attachments needs to be removed too
        # TODO therefore we need to know the structure of the attachments dir and which one has been added

    # helper function to create all the different image types and returns the file names of all generated images
    def create_images():
        # actual image color: 255,0,0
        img = Image.new("RGB", (100, 20), color='red')
        text = ImageDraw.Draw(img)
        text.text((10, 10), "Hello World", fill=(0, 0, 0))
        image_wmeta = 'image_wmeta'

        # thumbnail color: 0,0,255
        o = io.BytesIO()
        secret_thumbnail = Image.new("RGB", (120, 20), color='blue')
        text = ImageDraw.Draw(secret_thumbnail)
        text.text((10, 10), "secret thumbnail", fill=(0, 0, 0))
        # transform it to bytes
        secret_thumbnail.save(o, "jpeg")
        secret_exif_thumbnail = o.getvalue()
        secret_thumbnail.close()

        # forbidden image_extension
        img.save(forbidden_img, "tiff")
        # bmp doesn't contain critical meta information
        img.save(image_wmeta + "_bmp" + '.bmp')

        # for some reasons some of these values don't match the relative specification:
        # rational numbers are separated at the comma, f.e. 13.37 is represented by [(13), (37)]
        # http://www.cipa.jp/std/documents/e/DC-008-2012_E.pdf#page=47 ...
        # http://www.cipa.jp/std/documents/e/DC-008-2012_E.pdf#page=87
        jpg_exif = {
                    "0th": {
                             piexif.ImageIFD.ImageDescription: u"description",
                             piexif.ImageIFD.StripOffsets: 3,
                             piexif.ImageIFD.Artist: u"artist",
                             piexif.ImageIFD.Copyright: u"copyright holder",
                             piexif.ImageIFD.DateTime: u"2012:01:08 10:09:01",
                           },
                    "Exif": {
                             piexif.ExifIFD.DateTimeOriginal: u"2016:08:07 13:37:10",
                             piexif.ExifIFD.DateTimeDigitized: u"2015:03:07 14:20:30",
                             piexif.ExifIFD.OffsetTime: u"2017:05:09 08:04:04",
                             piexif.ExifIFD.OffsetTimeOriginal: u"2017:04:12 18:15:00",
                             piexif.ExifIFD.OffsetTimeDigitized: u"2016:02:10 11:10:03",
                             piexif.ExifIFD.SubSecTime: u"2017:09:04 10:03:10",
                             piexif.ExifIFD.SubSecTimeOriginal: u"2019:10:03 10:03:10",
                             piexif.ExifIFD.SubSecTimeDigitized: u"2013:10:03 10:03:10",
                             piexif.ExifIFD.CameraOwnerName: u"Cameraname",
                             piexif.ExifIFD.BodySerialNumber: u"body serialnumber",
                             piexif.ExifIFD.LensSerialNumber: u"lens serialnumber",
                             piexif.ExifIFD.UserComment: b"secret comment",
                           },
                    "GPS": {
                            piexif.GPSIFD.GPSLatitudeRef: u"N",
                            piexif.GPSIFD.GPSLatitude: [(10, 1), (20, 1), (0, 0)],
                            piexif.GPSIFD.GPSLongitudeRef: u"W",
                            piexif.GPSIFD.GPSLongitude: [(10, 1), (20, 1), (0, 0)],
                            piexif.GPSIFD.GPSAltitudeRef: 0,
                            piexif.GPSIFD.GPSAltitude: (200, 1),
                            piexif.GPSIFD.GPSTimeStamp: [(10), (3)],
                            piexif.GPSIFD.GPSSatellites: u"satellites",
                            piexif.GPSIFD.GPSStatus: u"A",
                            piexif.GPSIFD.GPSMeasureMode: u"3",
                            piexif.GPSIFD.GPSDOP: [(1), (4)],
                            piexif.GPSIFD.GPSSpeedRef: u"K",
                            piexif.GPSIFD.GPSSpeed: [(42), (10)],
                            piexif.GPSIFD.GPSTrackRef: u"T",
                            piexif.GPSIFD.GPSTrack: [(21), (123)],
                            piexif.GPSIFD.GPSImgDirectionRef: u"T",
                            piexif.GPSIFD.GPSImgDirection: [(10), (12)],
                            piexif.GPSIFD.GPSMapDatum: u"today",
                            piexif.GPSIFD.GPSDestLatitudeRef: u"N",
                            piexif.GPSIFD.GPSDestLatitude: [(8, 1), (30, 1), (0, 0)],
                            piexif.GPSIFD.GPSDestLongitudeRef: u"E",
                            piexif.GPSIFD.GPSDestLongitude: [(8), (30)],
                            piexif.GPSIFD.GPSDestBearingRef: u"T",
                            piexif.GPSIFD.GPSDestBearing: [(1), (10)],
                            piexif.GPSIFD.GPSDestDistanceRef: u"K",
                            piexif.GPSIFD.GPSDestDistance: [(10), (3)],
                            piexif.GPSIFD.GPSProcessingMethod: b"WLAN",
                            piexif.GPSIFD.GPSAreaInformation: b"area",
                            piexif.GPSIFD.GPSDateStamp:  u"2015:10:03 10:03:10",
                            piexif.GPSIFD.GPSDifferential: 1,
                            piexif.GPSIFD.GPSHPositioningError: [(2), (0)],
                           },
                    "1st": {
                             piexif.ImageIFD.ImageDescription: u"description",
                             piexif.ImageIFD.StripOffsets: 3,
                             piexif.ImageIFD.Artist: u"artist",
                             piexif.ImageIFD.Copyright: u"copyright holder",
                             piexif.ImageIFD.DateTime: u"2013:10:03 10:03:10",
                           },
                    "thumbnail": secret_exif_thumbnail
                    }

        png_dict = {
            "ImageDescription": u"description",
            "StripOffsets": "3",
            "Artist": u"artist",
            "Copyright": u"copyright holder",
            "DateTime": u"2012:01:08 10:09:01",
            "DateTimeOriginal": u"2016:08:07 13:37:10",
            "DateTimeDigitized": u"2015:03:07 14:20:30",
            "OffsetTime": u"2017:05:09 08:04:04",
            "OffsetTimeOriginal": u"2017:04:12 18:15:00",
            "OffsetTimeDigitized": u"2016:02:10 11:10:03",
            "SubSecTime": u"2017:09:04 10:03:10",
            "SubSecTimeOriginal": u"2019:10:03 10:03:10",
            "SubSecTimeDigitized": u"2013:10:03 10:03:10",
            "CameraOwnerName": u"Cameraname",
            "BodySerialNumber": u"body serialnumber",
            "LensSerialNumber": u"lens serialnumber",
            "UserComment": b"secret comment",
            "GPSLatitudeRef": u"N",
            "GPSLatitude": "3 deg 20' 0.00",
            "GPSLongitudeRef": u"W",
            "GPSLongitude": "3 deg 20.1' 0.00",
            "GPSAltitudeRef": "0",
            "GPSAltitude": "200 m Above Sea Level",
            "GPSTimeStamp": "03:19:59.999999",
            "GPSSatellites": u"satellites",
            "GPSStatus": u"A",
            "GPSMeasureMode": u"3",
            "GPSSpeedRef": u"K",
            "GPSSpeed": "4.2",
            "GPSTrackRef": u"T",
            "GPSTrack": "0.1707317073",
            "GPSImgDirectionRef": u"T",
            "GPSImgDirection": "0.6333333333",
            "GPSMapDatum": u"today",
            "GPSDestLatitudeRef": u"N",
            "GPSDestLatitude": "3 deg 30' 0.00",
            "GPSDestLongitudeRef": u"E",
            "GPSDestLongitude": "0 deg 16' 0.00",
            "GPSDestBearingRef": u"T",
            "GPSDestBearing": "0.1",
            "GPSDestDistanceRef": u"K",
            "GPSDestDistance": "3.333333333",
            "GPSProcessingMethod": b"WLAN",
            "GPSAreaInformation": b"area",
            "GPSDateStamp":  u"2015:10:03 10:03:10",
            "GPSDifferential": "1",
            "ImageDescription": u"description",
            "StripOffsets": "3",
            "Artist": u"artist",
            "Copyright": u"copyright holder",
            "DateTime": u"2013:10:03 10:03:10",
                    }

        # jpg with exif
        img.save(image_wmeta + '_jpg' + '.jpg', exif=piexif.dump(jpg_exif))
        # copy jpg to jpe, jpeg
        copyfile(image_wmeta + '_jpg' + '.jpg', image_wmeta + '_jpe' + '.jpe')
        copyfile(image_wmeta + '_jpg' + '.jpg', image_wmeta + '_jpeg' + '.jpeg')

        # png exif-part
        png_info = PngImagePlugin.PngInfo()
        # copy png metadata
        for k, v in png_dict.items():
            png_info.add_text(k, v, 0)
        img.save(image_wmeta + '_png' + '.png', "PNG", pnginfo=png_info)

        img.save(image_wmeta + '_gif' + '.gif')
        img.close()

        # xmp for gif and png
        xmp = XMPMeta()
        xmp.append_array_item(consts.XMP_NS_DC, 'secret', 'secret information',
                              {'prop_array_is_ordered': True, 'prop_value_is_array': True})

        # gif xmp
        # TODO BUG Exempi library version >= 2.5 does not work with GIF images created by Pillow.
        # TODO BUG The format gets not recognized by Exempi.
        # TODO BUG Maybe a newer Pillow or Exempi version will fix this...
        # gif_image = XMPFiles(file_path=image_wmeta + '_gif' + ".gif", open_forupdate=True)
        # gif_image.put_xmp(xmp)
        # gif_image.close_file()

        # png part 2
        png_image = XMPFiles(file_path=image_wmeta + '_png' + ".png", open_forupdate=True)
        png_image.put_xmp(xmp)
        png_image.close_file()

        return ((image_wmeta + '_' + suffix + "." + suffix) for suffix in ALLOWED_IMG_EXTENSIONS)

    def verify_metadatas_are_removed(self, file_path):
        # helper function that verifies that the provided image doesn't contain any sensitive metadata
        # empty exif
        self.assertEqual(piexif.load(file_path)["0th"], {}, msg="sensitive exif data left")
        self.assertEqual(piexif.load(file_path)["Exif"], {}, msg="sensitive exif data left")
        self.assertEqual(piexif.load(file_path)["GPS"], {}, msg="sensitive exif data left")
        self.assertEqual(piexif.load(file_path)["1st"], {}, msg="sensitive exif data left")
        # Imagine the following scenario: An image contains sensitive information, it gets modified to hide these.
        # If there is an exif-thumbnail it might represent the previous image and hence could leak those information.
        self.assertEqual(piexif.load(file_path)["thumbnail"], None, msg="The exif thumbnail has not been removed.")

        # verify that xmp is also empty. Normally the xmp content is stored in within the rdf tag
        xmp_file = XMPFiles(file_path=file_path)
        xmp_content = str(xmp_file.get_xmp())
        # this won't match if there are any additional xmp elements left, because they would occur between the opening
        # of the rdf:Description tag and the closing of the rdf:RDF tag.
        sensitive_information = re.findall("  <rdf:Description.*\n </rdf:RDF>", xmp_content)
        self.assertEqual(len(sensitive_information), 1,
                         msg="There are sensitive xmp-tags left:\n\n{}".format(xmp_content))
        xmp_file.close_file()

    def verify_images_are_sanitized(self, file_path):
        # helper function that verifies that the provided image is sanitized
        # TODO TESTCASE image sanitize check
        return True

    def test_change_avatar(self):
        # upload all prepared images
        for img_name in self.images:
            img = open(img_name, "rb")
            img_dict = {
                'avatar': img,
                'email': user_email,
                'timezone': timezone,
                'language': 'en',
            }
            response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}),
                                        img_dict, follow=True)
            img.close()

            # verify the file has been uploaded successfully
            file_name = os.path.basename(img_name).partition(".")[0]+".jpg"
            self.assertContains(response, file_name)
            file_path = avatars_path + "/" + file_name

            # verify there are no sensitive metadata left
            self.verify_metadatas_are_removed(file_path)
            # verify there is no malicious code left
            self.verify_images_are_sanitized(file_path)

    def test_comment_with_picture(self):
        # TODO TESTCASE comment with picture from issue-detail - picture stripping
        #               upload one image
        # TODO          call verify_metadatas_are_removed() and verify_images_are_sanitized()
        pass

    def test_file_upload_picture(self):
        # TODO TESTCASE attachment from issue-detail - picture stripping
        #               upload one image
        # TODO          call verify_metadatas_are_removed() and verify_images_are_sanitized()
        pass

    def test_change_user_profile_wo_default_avatar(self):
        # TODO TESTCASE create test that changes the user profile while the current avatar is not the default one
        #      this might produce some additional errors
        pass

    def test_reject_forbidden_img_extensions(self):
        # upload a forbidden img extensions
        img = open(forbidden_img, "rb")
        img_dict = {
            'avatar': img,
            'email': user_email,
            'timezone': timezone,
            'language': 'en',
        }
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}),
                                    img_dict, follow=True)
        img.close()
        # verify the file has NOT been uploaded successfully
        file_name = os.path.basename(forbidden_img).partition(".")[0]+".jpg"
        self.assertNotContains(response, file_name)
        self.assertContains(response, "is not allowed. Allowed extensions are:")

        # upload a forbidden img type with an allowed extensions
        file_name = 'trick.jpg'
        copyfile(forbidden_img, file_name)
        img = open(file_name, "rb")
        img_dict['avatar'] = img
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}),
                                    img_dict, follow=True)
        img.close()
        os.unlink(file_name)
        self.assertNotContains(response, file_name)
        self.assertContains(response, "Either unable to detect the image type or the image type is not supported. " +
                            "Supported image extensions are:")

    def test_file_size_limitation(self):
        # verify that the allowed image size (avatar) is actually limited
        huge_img = TEST_FILE_PATH+'/8mb.png'
        img = open(huge_img, "rb")
        img_dict = {
            'avatar': img,
            'email': user_email,
            'timezone': timezone,
            'language': 'en',
        }
        # TODO BUG ResourceWarning: unclosed file <_io.BufferedReader name='/tmp/tmp......upload.png'>
        #          seems to be a leak in Pillow
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}),
                                    img_dict, follow=True)
        img.close()
        self.assertContains(response, "The uploaded image exceeds the allowed file size of: ")

    def test_malicious_pictures(self):
        # TODO TESTCASE upload malicious image and verify it is harmless after upload
        pass
