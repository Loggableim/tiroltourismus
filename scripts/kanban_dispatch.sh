#!/bin/bash
cd E:/HermesPortable
HERMES_KANBAN_BOARD=tirol-uebersetzung PYTHONPATH=cids-hermes-agent python -m hermes_cli.main kanban dispatch 2>&1 | head -10

