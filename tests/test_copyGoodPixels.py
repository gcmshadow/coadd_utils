#
# LSST Data Management System
# Copyright 2008, 2009, 2010 LSST Corporation.
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.
#

"""Test lsst.coadd.utils.copyGoodPixels
"""
import unittest

import numpy as np

import lsst.utils.tests
import lsst.afw.geom as afwGeom
import lsst.afw.image as afwImage
import lsst.coadd.utils as coaddUtils
from lsst.log import Log

try:
    display
except NameError:
    display = False

Log.getLogger("coadd.utils").setLevel(Log.INFO)


def referenceCopyGoodPixelsImage(destImage, srcImage):
    """Reference implementation of lsst.coadd.utils.copyGoodPixels for Images

    Unlike lsst.coadd.utils.copyGoodPixels this one does not update the input destImage,
    but instead returns the new version

    Inputs:
    - destImage: source image before adding srcImage (a MaskedImage)
    - srcImage: masked image to add to destImage (a MaskedImage)
    - badPixelMask: mask of bad pixels to ignore (an int)

    Returns:
    - destImage: new destImage
    - numGoodPix: number of good pixels
    """
    destImage = destImage.Factory(destImage, True)  # make deep copy

    overlapBBox = destImage.getBBox()
    overlapBBox.clip(srcImage.getBBox())

    if overlapBBox.isEmpty():
        return (destImage, 0)

    destImageView = destImage.Factory(destImage, overlapBBox, afwImage.PARENT, False)
    destImageArray = destImageView.getArray()

    srcImageView = srcImage.Factory(srcImage, overlapBBox, afwImage.PARENT, False)
    srcImageArray = srcImageView.getArray()

    isBadArray = np.isnan(srcImageArray)

    destImageArray[:] = np.where(isBadArray, destImageArray, srcImageArray)
    numGoodPix = np.sum(np.logical_not(isBadArray))
    return destImage, numGoodPix


def referenceCopyGoodPixelsMaskedImage(destImage, srcImage, badPixelMask):
    """Reference implementation of lsst.coadd.utils.copyGoodPixels for MaskedImages

    Unlike lsst.coadd.utils.copyGoodPixels this one does not update the input destImage,
    but instead returns an updated copy

    @param[in] destImage: source image before adding srcImage (a MaskedImage)
    @param[in] srcImage: masked image to add to destImage (a MaskedImage)
    @param[in] badPixelMask: mask of bad pixels to ignore (an int)

    Returns:
    - destImage: new destImage
    - numGoodPix: number of good pixels
    """
    destImage = destImage.Factory(destImage, True)  # make deep copy

    overlapBBox = destImage.getBBox()
    overlapBBox.clip(srcImage.getBBox())

    if overlapBBox.isEmpty():
        return (destImage, 0)

    destImageView = destImage.Factory(destImage, overlapBBox, afwImage.PARENT, False)
    destImageArrayList = destImageView.getArrays()

    srcImageView = srcImage.Factory(srcImage, overlapBBox, afwImage.PARENT, False)
    srcImageArrayList = srcImageView.getArrays()

    isBadArray = (srcImageArrayList[1] & badPixelMask) != 0

    for ind in range(3):
        destImageView = destImageArrayList[ind]
        srcImageView = srcImageArrayList[ind]
        destImageView[:] = np.where(isBadArray, destImageView, srcImageView)
    numGoodPix = np.sum(np.logical_not(isBadArray))
    return destImage, numGoodPix


MaxMask = 0xFFFF


class CopyGoodPixelsTestCase(lsst.utils.tests.TestCase):
    """A test case for copyGoodPixels
    """

    def getSolidMaskedImage(self, bbox, val, badMask=0):
        afwDim = bbox.getDimensions()
        npShape = (afwDim[1], afwDim[0])

        np.random.seed(0)
        maskedImage = afwImage.MaskedImageF(bbox)
        imageArrays = maskedImage.getArrays()
        imageArrays[0][:] = val
        imageArrays[2][:] = val * 0.5
        imageArrays[1][:, 0:npShape[1]/2] = 0
        imageArrays[1][:, npShape[1]/2:] = badMask
        return maskedImage

    def getRandomMaskedImage(self, bbox, excludeMask=0):
        """Get a randomly generated masked image
        """
        if excludeMask > MaxMask:
            raise RuntimeError("excludeMask = %s > %s = MaxMask" % (excludeMask, MaxMask))

        afwDim = bbox.getDimensions()
        npShape = (afwDim[1], afwDim[0])

        np.random.seed(0)
        maskedImage = afwImage.MaskedImageF(bbox)
        imageArrays = maskedImage.getArrays()
        imageArrays[0][:] = np.random.normal(5000, 5000, npShape)  # image
        imageArrays[2][:] = np.random.normal(3000, 3000, npShape)  # variance
        imageArrays[1][:] = np.logical_and(np.random.randint(0, 8, npShape), ~excludeMask)
        return maskedImage

    def getRandomImage(self, bbox, nanSigma=0):
        """Get a randomly generated image
        """
        afwDim = bbox.getDimensions()
        npShape = (afwDim[1], afwDim[0])

        np.random.seed(0)
        image = afwImage.ImageF(bbox)
        imageArray = image.getArray()
        imageArray[:] = np.random.normal(5000, 5000, npShape)
        if nanSigma > 0:
            # add NaNs at nanSigma above mean of a test array
            nanTest = np.random.normal(0, 1, npShape)
            imageArray[:] = np.where(nanTest > nanSigma, np.nan, imageArray)
        return image

    def basicMaskedImageTest(self, srcImage, destImage, badMask):
        refDestImage, refNumGoodPix = referenceCopyGoodPixelsMaskedImage(destImage, srcImage, badMask)
        numGoodPix = coaddUtils.copyGoodPixels(destImage, srcImage, badMask)

        self.assertEqual(numGoodPix, refNumGoodPix)

        msg = "masked image != reference masked image"
        try:
            self.assertMaskedImagesAlmostEqual(destImage, refDestImage, msg=msg)
        except Exception:
            destImage.writeFits("destMaskedImage.fits")
            refDestImage.writeFits("refDestMaskedImage.fits")
            raise

    def basicImageTest(self, srcImage, destImage):
        refDestImage, refNumGoodPix = referenceCopyGoodPixelsImage(destImage, srcImage)
        numGoodPix = coaddUtils.copyGoodPixels(destImage, srcImage)

        msg = "image != reference image"
        try:
            self.assertImagesAlmostEqual(destImage, refDestImage, msg=msg)
        except Exception:
            destImage.writeFits("destImage.fits")
            refDestImage.writeFits("refDestImage.fits")
            raise

        self.assertEqual(numGoodPix, refNumGoodPix)

    def testMaskedImage(self):
        """Test image version of copyGoodPixels"""
        srcBBox = afwGeom.Box2I(afwGeom.Point2I(2, 17), afwGeom.Point2I(100, 101), invert=False)
        destBBox = afwGeom.Box2I(afwGeom.Point2I(13, 4), afwGeom.Point2I(95, 130), invert=False)
        destXY0 = destBBox.getMin()

        srcImage = self.getRandomMaskedImage(srcBBox)
        for badMask in (0, 3, MaxMask):
            destImage = self.getRandomMaskedImage(destBBox, excludeMask=badMask)
            destBBox = destImage.getBBox()
            self.basicMaskedImageTest(srcImage, destImage, badMask)

            for bboxStart in (destXY0, (50, 51)):
                for bboxDim in ((25, 36), (200, 200)):
                    destViewBox = afwGeom.Box2I(afwGeom.Point2I(*bboxStart), afwGeom.Extent2I(*bboxDim),
                                                invert=False)
                    destViewBox.clip(destBBox)
                    destView = destImage.Factory(destImage, destViewBox, afwImage.PARENT, False)
                    self.basicMaskedImageTest(srcImage, destView, badMask)

    def testImage(self):
        """Test image version of copyGoodPixels"""
        srcBBox = afwGeom.Box2I(afwGeom.Point2I(2, 17), afwGeom.Point2I(100, 101), invert=False)
        destBBox = afwGeom.Box2I(afwGeom.Point2I(13, 4), afwGeom.Point2I(95, 130), invert=False)
        destXY0 = destBBox.getMin()

        srcImage = self.getRandomImage(srcBBox)
        for nanSigma in (0, 0.7, 2.0):
            destImage = self.getRandomImage(destBBox, nanSigma=nanSigma)
            destBBox = destImage.getBBox()
            self.basicImageTest(srcImage, destImage)

            for bboxStart in (destXY0, (50, 51)):
                for bboxDim in ((25, 36), (200, 200)):
                    destViewBox = afwGeom.Box2I(afwGeom.Point2I(*bboxStart), afwGeom.Extent2I(*bboxDim),
                                                invert=False)
                    destViewBox.clip(destBBox)
                    destView = destImage.Factory(destImage, destViewBox, afwImage.PARENT, False)
                    self.basicImageTest(srcImage, destView)


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
