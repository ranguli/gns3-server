#
# Copyright (C) 2020 GNS3 Technologies Inc.
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
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""
API routes for compute.
"""

import os
import psutil

from gns3server.config import Config
from gns3server.utils.cpu_percent import CpuPercent
from gns3server.version import __version__
from gns3server.utils.path import get_default_project_directory
from gns3server.compute.port_manager import PortManager
from gns3server.compute.project_manager import ProjectManager
from gns3server.utils.interfaces import interfaces
from gns3server.compute.qemu import Qemu
from gns3server.compute.virtualbox import VirtualBox
from gns3server.compute.vmware import VMware
from gns3server import schemas

from fastapi import APIRouter, HTTPException, Body, status
from fastapi.encoders import jsonable_encoder
from uuid import UUID
from typing import Optional, List

router = APIRouter()


@router.post("/projects/{project_id}/ports/udp",
             status_code=status.HTTP_201_CREATED)
def allocate_udp_port(project_id: UUID) -> dict:
    """
    Allocate an UDP port on the compute.
    """

    pm = ProjectManager.instance()
    project = pm.get_project(str(project_id))
    m = PortManager.instance()
    udp_port = m.get_free_udp_port(project)
    return {"udp_port": udp_port}


@router.get("/network/interfaces")
def network_interfaces() -> dict:
    """
    List all the network interfaces available on the compute"
    """

    network_interfaces = interfaces()
    return network_interfaces


@router.get("/network/ports")
def network_ports() -> dict:
    """
    List all the ports used on the compute"
    """

    m = PortManager.instance()
    return m.__json__()


@router.get("/version")
def compute_version() -> dict:
    """
    Retrieve the server version number.
    """

    local_server = Config.instance().settings.Server.local
    return {"version": __version__, "local": local_server}


@router.get("/statistics")
def compute_statistics() -> dict:
    """
    Retrieve the server version number.
    """

    try:
        memory_total = psutil.virtual_memory().total
        memory_free = psutil.virtual_memory().available
        memory_used = memory_total - memory_free  # actual memory usage in a cross platform fashion
        swap_total = psutil.swap_memory().total
        swap_free = psutil.swap_memory().free
        swap_used = psutil.swap_memory().used
        cpu_percent = int(CpuPercent.get())
        load_average_percent = [int(x / psutil.cpu_count() * 100) for x in psutil.getloadavg()]
        memory_percent = int(psutil.virtual_memory().percent)
        swap_percent = int(psutil.swap_memory().percent)
        disk_usage_percent = int(psutil.disk_usage(get_default_project_directory()).percent)
    except psutil.Error as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        #raise HTTPConflict(text="Psutil error detected: {}".format(e))

    return {"memory_total": memory_total,
            "memory_free": memory_free,
            "memory_used": memory_used,
            "swap_total": swap_total,
            "swap_free": swap_free,
            "swap_used": swap_used,
            "cpu_usage_percent": cpu_percent,
            "memory_usage_percent": memory_percent,
            "swap_usage_percent": swap_percent,
            "disk_usage_percent": disk_usage_percent,
            "load_average_percent": load_average_percent}


@router.get("/qemu/binaries")
async def get_qemu_binaries(archs: Optional[List[str]] = Body(None, embed=True)):

    return await Qemu.binary_list(archs)


@router.get("/qemu/img-binaries")
async def get_image_binaries():

    return await Qemu.img_binary_list()


@router.get("/qemu/capabilities")
async def get_qemu_capabilities() -> dict:
    capabilities = {"kvm": []}
    kvms = await Qemu.get_kvm_archs()
    if kvms:
        capabilities["kvm"] = kvms
    return capabilities


@router.post("/qemu/img",
             status_code=status.HTTP_204_NO_CONTENT,
             responses={403: {"model": schemas.ErrorMessage, "description": "Forbidden to create Qemu image"}})
async def create_qemu_image(image_data: schemas.QemuImageCreate):
    """
    Create a Qemu image.
    """

    if os.path.isabs(image_data.path):
        if Config.instance().settings.Server.local is False:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    await Qemu.instance().create_disk(image_data.qemu_img, image_data.path, jsonable_encoder(image_data, exclude_unset=True))


@router.put("/qemu/img",
            status_code=status.HTTP_204_NO_CONTENT,
            responses={403: {"model": schemas.ErrorMessage, "description": "Forbidden to update Qemu image"}})
async def update_qemu_image(image_data: schemas.QemuImageUpdate):
    """
    Update a Qemu image.
    """

    if os.path.isabs(image_data.path):
        if Config.instance().settings.Server.local is False:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    if image_data.extend:
        await Qemu.instance().resize_disk(image_data.qemu_img, image_data.path, image_data.extend)


@router.get("/virtualbox/vms",
            response_model=List[dict])
async def get_virtualbox_vms():

    vbox_manager = VirtualBox.instance()
    return await vbox_manager.list_vms()


@router.get("/vmware/vms",
            response_model=List[dict])
async def get_vms():
    vmware_manager = VMware.instance()
    return await vmware_manager.list_vms()
