#
# LSST Data Management System
# Copyright 2008-2015 AURA/LSST.
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.
#
__all__ = ["CoaddDataIdContainer", "ExistingCoaddDataIdContainer"]

import argparse

import lsst.pipe.base as pipeBase


class CoaddDataIdContainer(pipeBase.DataIdContainer):
    """A version of lsst.pipe.base.DataIdContainer specialized for coaddition.

    Required because butler.subset does not support patch and tract

    This code was originally in pipe_tasks (coaddBase.py)
    """

    def getSkymap(self, namespace):
        """Only retrieve skymap if required"""
        if not hasattr(self, "_skymap"):
            self._skymap = namespace.butler.get(namespace.config.coaddName + "Coadd_skyMap")
        return self._skymap

    def makeDataRefList(self, namespace):
        """Make self.refList from self.idList
        """
        validKeys = namespace.butler.getKeys(datasetType=self.datasetType, level=self.level)

        for dataId in self.idList:
            for key in validKeys:
                if key in ("tract", "patch"):
                    # Will deal with these explicitly
                    continue
                if key not in dataId:
                    raise argparse.ArgumentError(None, "--id must include " + key)

            # tract and patch are required; iterate over them if not provided
            if "tract" not in dataId:
                if "patch" in dataId:
                    raise RuntimeError("'patch' cannot be specified without 'tract'")
                addList = [dict(tract=tract.getId(), patch="%d,%d" % patch.getIndex(), **dataId)
                           for tract in self.getSkymap(namespace) for patch in tract]
            elif "patch" not in dataId:
                tract = self.getSkymap(namespace)[dataId["tract"]]
                addList = [dict(patch="%d,%d" % patch.getIndex(), **dataId) for patch in tract]
            else:
                addList = [dataId]

            self.refList += [namespace.butler.dataRef(datasetType=self.datasetType, dataId=addId)
                             for addId in addList]


class ExistingCoaddDataIdContainer(CoaddDataIdContainer):
    """A version of CoaddDataIdContainer that only produces references that exist"""

    def makeDataRefList(self, namespace):
        super(ExistingCoaddDataIdContainer, self).makeDataRefList(namespace)
        self.refList = [ref for ref in self.refList if ref.datasetExists()]
