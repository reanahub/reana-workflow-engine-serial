# -*- coding: utf-8 -*-
#
# This file is part of REANA.
# Copyright (C) 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026 CERN.
#
# REANA is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""REANA Workflow Engine Serial tasks."""

from __future__ import absolute_import, print_function

import logging
from reana_commons.config import REANA_LOG_FORMAT, REANA_LOG_LEVEL
from reana_commons.serial import serial_load
from reana_commons.workflow_engine import create_workflow_engine_command

from .config import WORKFLOW_KERBEROS
from .utils import (
    build_job_spec,
    get_targeted_workflow_steps,
    poll_job_status,
    publish_job_submission,
    publish_job_success,
    publish_workflow_failure,
    publish_workflow_start,
)


def initialize(workflow_workspace):
    """Initialize engine."""
    # configure the logger
    logging.basicConfig(level=REANA_LOG_LEVEL, format=REANA_LOG_FORMAT)

    return workflow_workspace


def run(
    publisher,
    rjc_api_client,
    workflow_json,
    workflow_parameters,
    operational_options,
    workflow_uuid,
    workflow_workspace,
):
    """Run a serial workflow."""
    operational_options = operational_options or {}
    publish_workflow_start(workflow_json.get("steps", []), workflow_uuid, publisher)

    expanded_workflow_json = serial_load(None, workflow_json, workflow_parameters)
    steps_to_run = get_targeted_workflow_steps(
        expanded_workflow_json,
        operational_options.get("TARGET", None),
        operational_options.get("FROM", None),
    )
    workflow_json["steps"] = expanded_workflow_json["steps"] = steps_to_run

    for step_number, step in enumerate(steps_to_run):
        status = run_step(
            rjc_api_client,
            step_number,
            step,
            workflow_workspace,
            expanded_workflow_json,
            workflow_json,
            publisher,
            workflow_uuid,
        )
        if status != "finished":
            break


def run_step(
    rjc_api_client,
    step_number,
    step,
    workflow_workspace,
    expanded_workflow_json,
    workflow_json,
    publisher,
    workflow_uuid,
):
    """Run a step of a serial workflow."""
    for command in step["commands"]:
        job_spec = build_job_spec(
            job_name=step.get("name", ""),
            image=step["environment"],
            compute_backend=step.get("compute_backend", ""),
            command=command,
            workflow_workspace=workflow_workspace,
            workflow_uuid=workflow_uuid,
            kerberos=step.get("kerberos", WORKFLOW_KERBEROS),
            # Keep backwards compatibility for steps still using `unpacked_image`
            unpacked_img=step.get("unpacked_img", step.get("unpacked_image", False)),
            kubernetes_uid=step.get("kubernetes_uid"),
            kubernetes_cpu_request=step.get("kubernetes_cpu_request"),
            kubernetes_cpu_limit=step.get("kubernetes_cpu_limit"),
            kubernetes_memory_request=step.get("kubernetes_memory_request"),
            kubernetes_memory_limit=step.get("kubernetes_memory_limit"),
            kubernetes_job_timeout=step.get("kubernetes_job_timeout"),
            voms_proxy=step.get("voms_proxy", False),
            rucio=step.get("rucio", False),
            htcondor_max_runtime=step.get("htcondor_max_runtime", ""),
            htcondor_accounting_group=step.get("htcondor_accounting_group", ""),
            htcondor_request_cpus=step.get("htcondor_request_cpus", ""),
            htcondor_request_memory=step.get("htcondor_request_memory", ""),
            htcondor_request_disk=step.get("htcondor_request_disk", ""),
            htcondor_requirements=step.get("htcondor_requirements", ""),
            slurm_partition=step.get("slurm_partition"),
            slurm_time=step.get("slurm_time"),
            c4p_cpu_cores=step.get("c4p_cpu_cores"),
            c4p_memory_limit=step.get("c4p_memory_limit"),
            c4p_additional_requirements=step.get("c4p_additional_requirements"),
        )
        response = rjc_api_client.submit(**job_spec)
        job_id = str(response["job_id"])
        publish_job_submission(
            step_number, command, workflow_json, job_id, publisher, workflow_uuid
        )

        job_status = poll_job_status(rjc_api_client, job_id)
        if job_status.status == "finished":
            publish_job_success(
                job_id,
                expanded_workflow_json,
                step,
                command,
                publisher,
                workflow_uuid,
            )
        else:
            publish_workflow_failure(job_id, workflow_uuid, publisher)
            return job_status.status
    return job_status.status


def run_serial_workflow_engine_adapter(
    publisher,
    rjc_api_client,
    workflow_uuid=None,
    workflow_json=None,
    workflow_workspace=None,
    workflow_parameters=None,
    operational_options=None,
    **kwargs
):
    """Run a serial workflow."""
    workflow_workspace = initialize(workflow_workspace)

    run(
        publisher,
        rjc_api_client,
        workflow_json,
        workflow_parameters,
        operational_options,
        workflow_uuid,
        workflow_workspace,
    )


run_serial_workflow = create_workflow_engine_command(
    run_serial_workflow_engine_adapter, engine_type="serial"
)
