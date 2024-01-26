# -*- coding: utf-8 -*-
"""
Tests for the VDES1000 Transceiver Module

@author: Jan Safar

Copyright 2024 GLA Research and Development Directorate

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""
# =============================================================================
# %% Import Statements
# =============================================================================
# Built-in Modules ------------------------------------------------------------
from unittest.mock import MagicMock

# Third-party Modules ---------------------------------------------------------
import pytest
from bitstring import BitStream

# Local Modules ---------------------------------------------------------------
from vdes1000.trx import VDESTransceiver

# =============================================================================
# %% Test Fixtures
# =============================================================================
@pytest.fixture
def cfg():
    cfg = {"user": {"ip_address": "10.0.2.203",
                    "dest_port_misc": 60030,
                    "dest_port_aist": 60031,
                    "dest_port_ccrd": 60033,
                    "listen_misc": True,
                    "listen_aist": True,
                    "listen_ccrd": False,
                    "talker_id": "1",
                    "udp_buffer_size": 4096,
                    "udp_verbosity": 3}}

    return cfg

@pytest.fixture
def mock_udp_interface(monkeypatch):
    # Mock the UDPInterface class
    mock_udp_interface = MagicMock()
    monkeypatch.setattr("vdes1000.trx.UDPInterface", mock_udp_interface)

    # Mock specific attributes of the UDPInterface instance
    mock_udp_interface_instance = MagicMock()
    mock_udp_interface_instance.n_rx_threads = 2
    mock_udp_interface_instance.n_listening_ports = 2
    mock_udp_interface.return_value = mock_udp_interface_instance

    return mock_udp_interface

# =============================================================================
# %% Test Cases
# =============================================================================
def test_vdes_transceiver_initialization(cfg, mock_udp_interface):
    # Instantiate the VDESTransceiver
    transceiver = VDESTransceiver(cfg)

    # Check if the UDPInterface was initialized with the correct parameters
    mock_udp_interface.assert_called_once_with(
        ip_address=cfg["user"]["ip_address"],
        dest_port_misc=cfg["user"]["dest_port_misc"],
        dest_port_aist=cfg["user"]["dest_port_aist"],
        dest_port_ccrd=cfg["user"]["dest_port_ccrd"],
        listen_misc=cfg["user"]["listen_misc"],
        listen_aist=cfg["user"]["listen_aist"],
        listen_ccrd=cfg["user"]["listen_ccrd"],
        recv_cbk_misc=None,
        recv_cbk_aist=None,
        buffer_size=cfg["user"]["udp_buffer_size"],
        verbosity=cfg["user"]["udp_verbosity"])

def test_send_ais_msg(cfg, mock_udp_interface):
    # Set up the VDESTransceiver instance with mocked components
    trx = VDESTransceiver(cfg)
    trx.udp_interface = mock_udp_interface

    # Set up parameters for send_ais_msg
    msg_bs = BitStream(168)
    channel = "AIS 1"

    # Call the method
    trx.send_ais_msg(msg_bs, channel)

    # Check if the necessary methods were called
    calls = mock_udp_interface.send_misc_iec_msg.call_args_list
    assert len(calls) == 2
    assert calls[0][0][0] == "\\g:1-1-1,s:1*38\\$AITSA,,0,A,,,2*0D\r\n"
    assert calls[1][0][0] == "\\g:1-1-2,s:1*3B\\!AIVDM,1,1,0,A,0000000000000000000000000000,0*16\r\n"

def test_send_ais_binary_broadcast(cfg, mock_udp_interface):
    # Set up the VDESTransceiver instance with mocked components
    trx = VDESTransceiver(cfg)
    trx.udp_interface = mock_udp_interface

    # Set up parameters for send_ais_binary_broadcast
    asm_payload_bs = BitStream(64)
    channel = "AIS 1"

    # Call the method
    trx.send_ais_binary_broadcast(asm_payload_bs, channel)

    # Check if the necessary methods were called
    mock_udp_interface.send_misc_iec_msg.assert_called_once_with(
        "\\g:1-1-1,s:1*38\\!AIBBM,1,1,0,1,8,00000000000,2*52\r\n")

def test_send_asm_broadcast(cfg, mock_udp_interface):
    # Set up the VDESTransceiver instance with mocked components
    trx = VDESTransceiver(cfg)
    trx.udp_interface = mock_udp_interface

    # Set up parameters for send_asm_broadcast
    asm_payload_bs = BitStream(64)
    source_id = 123456789
    channel = "ASM 1"
    transmission_format = 0

    # Call the method
    trx.send_asm_broadcast(
        asm_payload_bs,
        source_id,
        channel,
        transmission_format)

    # Check if the necessary methods were called
    mock_udp_interface.send_misc_iec_msg.assert_called_once_with(
        "\\g:1-1-1,s:1*38\\!AIABB,01,01,0,123456789,1,,0,00000000000,2*67\r\n")

def test_send_vde_data(cfg, mock_udp_interface):
    # Set up the VDESTransceiver instance with mocked components
    trx = VDESTransceiver(cfg)
    trx.udp_interface = mock_udp_interface

    # Set up parameters for send_asm_broadcast
    pi_data_payload_bs = BitStream(64)
    destination_id = 123456789

    # Call the method
    trx.send_vde_data(
        pi_data_payload_bs,
        destination_id)

    # Check if the necessary methods were called
    mock_udp_interface.send_misc_iec_msg.assert_called_once_with(
        "\\g:1-1-1,s:1*38\\$AIEDM,0,,123456789,00000000000,2*6B\r\n")


# =============================================================================
# %% Main Fuction
# =============================================================================
if __name__ == '__main__':
    pytest.main()
