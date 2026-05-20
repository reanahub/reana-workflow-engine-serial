# -*- coding: utf-8 -*-
#
# This file is part of REANA.
# Copyright (C) 2026 CERN.
#
# REANA is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""REANA Workflow Engine Serial tasks tests."""

import pytest
from unittest.mock import MagicMock, patch

from reana_workflow_engine_serial.tasks import run_step


@pytest.mark.parametrize(
    "step_extra,expected",
    [
        ({"unpacked_img": True}, True),
        ({"unpacked_image": True}, True),
        ({"unpacked_img": True, "unpacked_image": False}, True),
        ({}, False),
    ],
    ids=[
        "unpacked_img_true",
        "legacy_unpacked_image_true",
        "both_present_unpacked_img_wins",
        "missing_defaults_to_false",
    ],
)
def test_run_step_unpacked_img_mapping(step_extra, expected):
    """Test that run_step passes the correct unpacked_img value to build_job_spec."""
    step = {"environment": "busybox", "commands": ["echo test"], **step_extra}
    workflow_json = {"steps": [step]}

    job_status = MagicMock()
    job_status.status = "finished"

    with (
        patch("reana_workflow_engine_serial.tasks.build_job_spec") as mock_build,
        patch(
            "reana_workflow_engine_serial.tasks.poll_job_status",
            return_value=job_status,
        ),
        patch("reana_workflow_engine_serial.tasks.publish_job_submission"),
        patch("reana_workflow_engine_serial.tasks.publish_job_success"),
    ):
        mock_build.return_value = {}
        rjc_client = MagicMock()
        rjc_client.submit.return_value = {"job_id": "test-id"}

        run_step(
            rjc_api_client=rjc_client,
            step_number=0,
            step=step,
            workflow_workspace="/workspace",
            cache_enabled=False,
            expanded_workflow_json=workflow_json,
            workflow_json=workflow_json,
            publisher=MagicMock(),
            workflow_uuid="test-uuid",
        )

    assert mock_build.call_args.kwargs["unpacked_img"] == expected
