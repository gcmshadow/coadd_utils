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
__all__ = ["makeBitMask"]

import lsst.afw.image as afwImage


def makeBitMask(maskPlaneNameList, doInvert=False):
    """Generate a bit mask consisting of ORed together Mask bit planes

    deprecated : use afwImage.Mask.getPlaneBitMask(maskPlaneNameList) instead.

    Parameters
    ----------
    maskPlaneNameList :
        list of mask plane names
    doInvert :
        if True then invert the result

    Returns
    -------
    bitmask :
        a bit mask consisting of the named bit planes ORed together (with the result possibly inverted)
    """
    bitMask = afwImage.Mask.getPlaneBitMask(maskPlaneNameList)
    if doInvert:
        bitMask = (2**afwImage.Mask.getNumPlanesMax() - 1) - bitMask
    return bitMask
