# -*- coding: utf-8 -*-
#
# This file is part of REANA.
# Copyright (C) 2018 CERN.
#
# REANA is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# REANA is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with REANA; if not, see <http://www.gnu.org/licenses>.
#
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization or
# submit itself to any jurisdiction.

"""REST API client generator."""

import json
import os

import pkg_resources
from bravado.client import SwaggerClient

from .config import COMPONENTS_DATA


def get_spec(spec_file):
    """Get json specification from package data."""
    spec_file_path = os.path.join(
        pkg_resources.
        resource_filename(
            'reana_workflow_engine_serial',
            'openapi_connections'),
        spec_file)

    with open(spec_file_path) as f:
        json_spec = json.load(f)
    return json_spec


def create_openapi_client(component):
    """Create a OpenAPI client for a given spec."""
    try:
        address, spec_file = COMPONENTS_DATA[component]
        json_spec = get_spec(spec_file)
        client = SwaggerClient.from_spec(
            json_spec,
            config={'also_return_response': True})
        client.swagger_spec.api_url = address
        return client
    except KeyError:
        raise Exception('Unkown component {}'.format(component))
