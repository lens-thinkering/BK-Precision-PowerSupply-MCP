"""Tests for the connection layer."""

from unittest.mock import MagicMock, patch

import pytest

from bk_precision_mcp.connection import get_resource_manager, list_resources


@patch("bk_precision_mcp.connection.pyvisa.ResourceManager")
def test_get_resource_manager_singleton(mock_rm_cls):
    import bk_precision_mcp.connection as conn

    conn._rm = None  # reset singleton
    rm1 = get_resource_manager()
    rm2 = get_resource_manager()
    assert rm1 is rm2
    mock_rm_cls.assert_called_once_with("@py")
    conn._rm = None  # cleanup


@patch("bk_precision_mcp.connection.pyvisa.ResourceManager")
def test_list_resources(mock_rm_cls):
    import bk_precision_mcp.connection as conn

    conn._rm = None
    mock_rm = MagicMock()
    mock_rm.list_resources.return_value = ("USB0::0x1234::0x5678::INSTR",)
    mock_rm_cls.return_value = mock_rm

    resources = list_resources()
    assert resources == ["USB0::0x1234::0x5678::INSTR"]
    conn._rm = None  # cleanup
