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

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from uuid import UUID

from .common import Label


class LinkNode(BaseModel):
    """
    Link node data.
    """

    node_id: UUID
    adapter_number: int
    port_number: int
    label: Optional[Label]


class LinkType(str, Enum):
    """
    Link type.
    """

    ethernet = "ethernet"
    serial = "serial"


class Link(BaseModel):
    """
    Link data.
    """

    link_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    nodes: Optional[List[LinkNode]] = None
    suspend: Optional[bool] = None
    filters: Optional[dict] = None
    capturing: Optional[bool] = Field(None, description="Read only property. True if a capture running on the link")
    capture_file_name: Optional[str] = Field(None, description="Read only property. The name of the capture file if a capture is running")
    capture_file_path: Optional[str] = Field(None, description="Read only property. The full path of the capture file if a capture is running")
    capture_compute_id: Optional[str] = Field(None, description="Read only property. The compute identifier where a capture is running")
    link_type: Optional[LinkType] = None